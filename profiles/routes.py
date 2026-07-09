"""Profile routes — save cycle profile and upload an avatar image."""
import os
import json
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from database.db import db_query

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "avatars")
ALLOWED_EXT   = {"png", "jpg", "jpeg", "webp", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@profile_bp.post("")
@login_required
def save_profile():
    data = request.json or {}
    db_query(
        "UPDATE users SET name=%s, last_period=%s, cycle_len=%s, period_len=%s WHERE id=%s",
        (data.get("name"), data.get("lastPeriod"), data.get("cycleLen", 28),
         data.get("periodLen", 5), current_user.id),
        write=True,
    )
    # persist notification preferences only when the client sends them,
    # so an onboarding save (no prefs) doesn't wipe existing ones
    if data.get("notifPrefs") is not None:
        db_query("UPDATE users SET notif_prefs=%s WHERE id=%s",
                 (json.dumps(data["notifPrefs"]), current_user.id), write=True)
    return jsonify({"ok": True})


@profile_bp.post("/avatar")
@login_required
def upload_avatar():
    f = request.files.get("avatar")
    if not f:
        return jsonify({"error": "No file provided"}), 400
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED_EXT:
        return jsonify({"error": "Invalid file type"}), 400
    filename = f"user_{current_user.id}.{ext}"
    f.save(os.path.join(UPLOAD_FOLDER, filename))
    url = f"/static/avatars/{filename}"
    db_query("UPDATE users SET avatar=%s WHERE id=%s", (url, current_user.id), write=True)
    return jsonify({"ok": True, "url": url})
