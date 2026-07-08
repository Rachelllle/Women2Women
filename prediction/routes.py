"""Prediction routes — next-period date and current cycle day/phase."""
from datetime import date, timedelta
from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from database.db import db_query
from recommandation.model import day_to_phase

prediction_bp = Blueprint("prediction", __name__, url_prefix="/api")


@prediction_bp.post("/predict")
@login_required
def predict():
    row = db_query(
        "SELECT last_period, cycle_len, period_len FROM users WHERE id = %s",
        (current_user.id,), one=True
    )
    if not row or not row["last_period"]:
        return jsonify({"error": "No cycle data saved"}), 400

    last = date.fromisoformat(str(row["last_period"]))   # SQLite stores dates as TEXT
    clen = row["cycle_len"] or 28
    plen = row["period_len"] or 5

    today        = date.today()
    days_since   = (today - last).days
    day_in_cycle = (days_since % clen) + 1
    phase        = day_to_phase(day_in_cycle, clen)

    next_period  = last + timedelta(days=((days_since // clen) + 1) * clen)
    days_to_next = (next_period - today).days

    return jsonify({
        "date":       str(next_period),
        "daysToNext": days_to_next,
        "dayInCycle": day_in_cycle,
        "phase":      phase,
        "cycleLen":   clen,
        "periodLen":  plen,
    })
