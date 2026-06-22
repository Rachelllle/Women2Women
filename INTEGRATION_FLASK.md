# Intégration du chatbot Hearts & Care dans le Flask

## Fichiers à récupérer depuis le repo Git

Place ces éléments dans le dossier du backend Flask (au même niveau que `app.py`) :

- `chatbot.py`                  → le module du chatbot (logique Qwen + LoRA + RAG)
- `hearts_care_qwen_lora/`      → dossier des adaptateurs LoRA
- `hearts_care_index.faiss`     → index RAG
- `hearts_care_chunks.json`     → fiches du RAG

## Installation des dépendances

Dans l'environnement Python du Flask :

```bash
pip install torch transformers peft sentence-transformers faiss-cpu
```

## Modification de app.py (Flask)

L'endpoint `/api/chat` existe déjà mais renvoie un stub. Il faut juste le brancher.

**En haut du fichier**, avec les autres imports, ajouter :

```python
from chatbot import get_chatbot_reply
```

**Puis remplacer la fonction chat() existante** :

```python
# AVANT (le stub)
@app.post("/api/chat")
@login_required
def chat():
    data    = request.json or {}
    message = data.get("message", "")
    ctx     = data.get("ctx", {})
    reply   = f"(stub) You said '{message}' on day {ctx.get('day')} ({ctx.get('phase')} phase)."
    return jsonify({"reply": reply})
```

```python
# APRÈS (branché sur le vrai chatbot)
@app.post("/api/chat")
@login_required
def chat():
    data    = request.json or {}
    message = data.get("message", "")
    reply   = get_chatbot_reply(message)
    return jsonify({"reply": reply})
```

C'est tout. Le frontend (composant Vera dans le HTML) appelle déjà `/api/chat`,
donc rien à changer côté interface.

## Note sur le premier appel

Le tout premier message sera lent (~30 s) : le modèle se charge en mémoire.
Tous les messages suivants seront rapides (le modèle reste en cache).
Pour la démo, envoyer un premier message "de chauffe" avant que le jury teste.

## Vérification avant la démo

Tester le module seul, sans Flask :

```bash
python chatbot.py
```

Si ça affiche des réponses cohérentes aux 3 questions de test, l'intégration
fonctionnera.
