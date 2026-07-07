from flask import Flask, request, jsonify, send_from_directory
from database.admin_panel import admin_bp
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql, os
from database.db import db_query
from recommandation.model import get_recommendations
from alerting.routes import alerting_bp

app = Flask(__name__)
app.secret_key = "change-me-before-deploying"
CORS(app, supports_credentials=True)
app.register_blueprint(admin_bp)
app.register_blueprint(alerting_bp)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def init_db():
    db_query("""
        CREATE TABLE IF NOT EXISTS users (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            email         VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """, write=True)

init_db()

login_manager = LoginManager(app)

class User(UserMixin):
    def __init__(self, id, email):
        self.id    = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    row = db_query("SELECT id, email FROM users WHERE id = %s", (user_id,), one=True)
    return User(row["id"], row["email"]) if row else None

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Login required"}), 401


@app.post("/api/auth/register")
def register():
    data     = request.json or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    try:
        db_query("INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                 (email, generate_password_hash(password)), write=True)
        return jsonify({"ok": True}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"error": "Email already registered"}), 409


@app.post("/api/auth/login")
def login():
    data     = request.json or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    row = db_query("SELECT id, email, password_hash FROM users WHERE email = %s", (email,), one=True)
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401
    login_user(User(row["id"], row["email"]))
    return jsonify({"ok": True, "email": row["email"]})


@app.post("/api/auth/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@app.get("/api/auth/me")
def me():
    if current_user.is_authenticated:
        row = db_query("SELECT name, last_period, cycle_len, period_len FROM users WHERE id = %s",
                       (current_user.id,), one=True)
        return jsonify({
            "id":        current_user.id,
            "email":     current_user.email,
            "name":      row["name"],
            "lastPeriod": str(row["last_period"]) if row["last_period"] else None,
            "cycleLen":  row["cycle_len"],
            "periodLen": row["period_len"],
        })
    return jsonify({"error": "Not logged in"}), 401


@app.post("/api/profile")
@login_required
def save_profile():
    data = request.json or {}
    db_query(
        "UPDATE users SET name=%s, last_period=%s, cycle_len=%s, period_len=%s WHERE id=%s",
        (data.get("name"), data.get("lastPeriod"), data.get("cycleLen", 28),
         data.get("periodLen", 5), current_user.id),
        write=True,
    )
    return jsonify({"ok": True})


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "Women2Women.html")


@app.post("/api/chat")
@login_required
def chat():
    data    = request.json or {}
    message = data.get("message", "")
    ctx     = data.get("ctx", {})
    reply   = f"(stub) You said '{message}' on day {ctx.get('day')} ({ctx.get('phase')} phase)."
    return jsonify({"reply": reply})


def day_to_phase(day, cycle_len=28):
    if day <= 5:                  return "menstrual"
    if day <= cycle_len // 2:     return "follicular"
    if day <= cycle_len // 2 + 3: return "ovulation"
    return "luteal"

@app.get("/api/recommendations")
def recommendations():
    day        = int(request.args.get("day", 14))
    phase      = request.args.get("phase") or day_to_phase(day)
    feeling    = request.args.get("feeling", "")
    cycle_len  = int(request.args.get("cycleLen", 28))
    period_len = int(request.args.get("periodLen", 5))
    return jsonify(get_recommendations(day, phase, feeling, cycle_len, period_len))


@app.post("/api/predict")
@login_required
def predict():
    return jsonify({"date": "2026-06-01", "daysToNext": 17, "confidence": 0.82})


@app.get("/api/alerts")
@login_required
def alerts():
    return jsonify([
        {"id": 1, "kind": "period", "urgent": True,  "when": "in 2 days",
         "title": "Your period is expected soon",
         "body": "Pack the essentials. Day 1 predicted Mon, 1 Jun.", "unread": True},
        {"id": 2, "kind": "phase",  "urgent": False, "when": "today",
         "title": "You're entering your luteal phase",
         "body": "Energy may dip toward the end of this week.", "unread": True},
    ])


if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
