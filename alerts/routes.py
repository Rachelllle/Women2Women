"""Alert routes — personalized cycle alerts (stub data for now)."""
from flask import Blueprint, jsonify
from flask_login import login_required

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api")


@alerts_bp.get("/alerts")
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
