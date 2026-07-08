# Women2Women

A cycle-tracking web app with personalized daily recommendations based on the user's menstrual phase, period prediction, and a cycle companion chatbot (Vera). Built with Flask and React.

## Requirements

- Python 3.10+
- No database server needed — the app uses **SQLite** (a single `women2women.db`
  file is created automatically on first run).

Install dependencies:
```bash
pip install flask flask-cors flask-login werkzeug sentence-transformers
# Vera chatbot (Qwen + LoRA + RAG):
pip install torch transformers "peft>=0.19.1" "accelerate>=1.0" faiss-cpu
```

> First chat message downloads the Qwen base model (~1 GB) and loads it into
> memory (~30 s). Subsequent messages are fast.

## How to Run

```bash
python app.py
```

- App: `http://localhost:5000`
- Admin panel: `http://localhost:5000/admin` (password: `admin123`)
