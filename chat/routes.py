"""Chat routes — Vera companion, powered by Nassilya's Hearts & Care chatbot.

Wires the /api/chat endpoint to the RAG + Qwen/LoRA model in chat/chatbot.py
(get_chatbot_reply). If that module or its heavy dependencies are unavailable,
we fall back to a stub so the app still runs.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

try:
    from chat.chatbot import get_chatbot_reply
    _CHATBOT_OK = True
except Exception as e:          # missing deps / model files → keep the app running
    _CHATBOT_OK = False
    _IMPORT_ERROR = str(e)


@chat_bp.post("/chat")
@login_required
def chat():
    data    = request.json or {}
    message = data.get("message", "")
    ctx     = data.get("ctx", {})

    if _CHATBOT_OK:
        reply = get_chatbot_reply(message)
    else:
        reply = (f"(stub) You said '{message}' on day {ctx.get('day')} "
                 f"({ctx.get('phase')} phase).")
    return jsonify({"reply": reply})
