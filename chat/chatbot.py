import os
import json
import torch
import faiss
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
LORA_PATH = os.path.join(BASE_DIR, "hearts_care_qwen_lora")
INDEX_FILE = os.path.join(BASE_DIR, "hearts_care_index.faiss")
CHUNKS_FILE = os.path.join(BASE_DIR, "hearts_care_chunks.json")
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 3
SCORE_THRESHOLD = 0.38

SYSTEM_PROMPT = (
    "You are Hearts & Care, a caring AI assistant specialized in women's hormonal "
    "and menstrual health. "
    "Answer the question using ONLY the information in the medical context below. "
    "Do NOT add facts that are not in the context. Do NOT use your own general knowledge. "
    "Keep your answer short (2-3 sentences maximum) and directly based on the context. "
    "If the context does not contain the answer, say you don't have reliable information "
    "and suggest seeing a healthcare professional."
)

_CACHE = {"loaded": False}


def _load():
    """Charge le modèle, l'embedder et l'index. Appelé une seule fois."""
    if _CACHE["loaded"]:
        return

    print("[chatbot] Chargement du modèle Hearts & Care...")
    tokenizer = AutoTokenizer.from_pretrained(LORA_PATH)
    base = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    model = PeftModel.from_pretrained(base, LORA_PATH)
    model.eval()
    model = model.to("cpu")

    embedder = SentenceTransformer(EMBED_MODEL_NAME)
    index = faiss.read_index(INDEX_FILE)
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    _CACHE.update({
        "tokenizer": tokenizer, "model": model, "embedder": embedder,
        "index": index, "chunks": chunks, "loaded": True,
    })
    print("[chatbot] Modèle prêt.")


def _retrieve(query, k=TOP_K):
    """RAG : retourne les k fiches les plus proches sous forme (texte, score)."""
    emb = _CACHE["embedder"].encode([query], convert_to_numpy=True,
                                    normalize_embeddings=True).astype("float32")
    scores, idxs = _CACHE["index"].search(emb, k)
    return [(_CACHE["chunks"][i], float(s))
            for s, i in zip(scores[0], idxs[0]) if i != -1]


def get_chatbot_reply(user_message):
    """
    Fonction principale appelée par Flask.
    Prend le message de l'utilisatrice, retourne la réponse texte du chatbot.
    """
    _load() 

    if not user_message or not user_message.strip():
        return "Please ask me a question about your cycle or symptoms."

    retrieved = _retrieve(user_message)

    if not retrieved or retrieved[0][1] < SCORE_THRESHOLD:
        return ("I'm not sure I have reliable information on that. Could you rephrase, "
                "or ask about a specific topic (cramps, cycle length, PMS, ovulation...)? "
                "For personal concerns, please consult a healthcare professional.")

    context_text = "\n".join(f"- {f}" for f, _ in retrieved)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",
         "content": f"Medical context:\n{context_text}\n\nQuestion: {user_message}"},
    ]
    tokenizer = _CACHE["tokenizer"]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=True)

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
    inputs = {k: v.to("cpu") for k, v in inputs.items()}

    with torch.no_grad():
        out = _CACHE["model"].generate(
            **inputs,
            max_new_tokens=100,
            do_sample=True,
            temperature=0.1,
            top_p=0.9,
            repetition_penalty=1.2,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = out[0][inputs["input_ids"].shape[1]:]
    answer = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    if not answer:
        answer = "I'm not sure. Please consider talking to a healthcare professional."
    return answer


#Test rapide en ligne de commande 
if __name__ == "__main__":
    for q in ["how long is a period?", "what is ovulation?", "i'm angry"]:
        print(f"\nQ: {q}\nA: {get_chatbot_reply(q)}")