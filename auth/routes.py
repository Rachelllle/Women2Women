"""Auth routes — register, login, logout, password reset, and current user."""
import sqlite3
import json
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import db_query
from auth import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
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
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered"}), 409


@auth_bp.post("/login")
def login():
    data     = request.json or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    row = db_query("SELECT id, email, password_hash FROM users WHERE email = %s", (email,), one=True)
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401
    login_user(User(row["id"], row["email"]), remember=True)
    return jsonify({"ok": True, "email": row["email"]})


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_bp.post("/reset-password")
def reset_password():
    data     = request.json or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error": "Email and new password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    row = db_query("SELECT id FROM users WHERE email = %s", (email,), one=True)
    if not row:
        return jsonify({"error": "No account found with this email"}), 404
    db_query("UPDATE users SET password_hash = %s WHERE email = %s",
             (generate_password_hash(password), email), write=True)
    return jsonify({"ok": True})


@auth_bp.get("/me")
def me():
    if current_user.is_authenticated:
        row = db_query("SELECT name, last_period, cycle_len, period_len, avatar, notif_prefs FROM users WHERE id = %s",
                       (current_user.id,), one=True)
        try:
            notif_prefs = json.loads(row["notif_prefs"]) if row["notif_prefs"] else None
        except (ValueError, TypeError):
            notif_prefs = None
        return jsonify({
            "id":         current_user.id,
            "email":      current_user.email,
            "name":       row["name"],
            "lastPeriod": str(row["last_period"]) if row["last_period"] else None,
            "cycleLen":   row["cycle_len"],
            "periodLen":  row["period_len"],
            "avatar":     row["avatar"],
            "notifPrefs": notif_prefs,
        })
    return jsonify({"error": "Not logged in"}), 401
