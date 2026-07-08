"""Cycle history & period logging (Katia's feature, made coherent).

Logging a period does three logical things, in order:
  1. VALIDATE the date (not future, strictly after the last period).
  2. ARCHIVE the cycle that just ended (duration = new start - previous start).
  3. LEARN: recompute the user's cycle_len as the average of recent history.

cycle_history is the single source of truth for past cycles; after any change
the alerting engine's `cycles` table is rebuilt from it (sync_cycles_from_history).
SQLite stores dates as TEXT, so dates are parsed from ISO strings. Placeholders
stay %s — database.db translates them to ?.
"""
from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from database.db import db_query
from alerting.db_bridge import sync_cycles_from_history

history_bp = Blueprint("history", __name__, url_prefix="/api")

MIN_CYCLE, MAX_CYCLE   = 15, 60   # plausible bounds for the cycle length
MIN_PERIOD, MAX_PERIOD = 2, 12    # plausible bounds for the period length
HISTORY_WINDOW         = 6        # average over the most recent N cycles


def _learned_cycle_len(user_id, fallback):
    """Average of recent archived cycles, clamped to a sane range."""
    rows = db_query(
        "SELECT cycle_len FROM cycle_history "
        "WHERE user_id = %s AND cycle_len > 0 "
        "ORDER BY start_date DESC LIMIT %s",
        (user_id, HISTORY_WINDOW),
    )
    lengths = [r["cycle_len"] for r in rows]
    if not lengths:
        return fallback
    avg = round(sum(lengths) / len(lengths))
    return max(MIN_CYCLE, min(MAX_CYCLE, avg))


def _clamp(v, lo, hi, default):
    try:
        return max(lo, min(hi, int(v)))
    except (ValueError, TypeError):
        return default


@history_bp.post("/period/log")
@login_required
def log_period():
    data     = request.json or {}
    date_str = data.get("date")

    # 1 ─ validate the input date
    if not date_str:
        return jsonify({"error": "Please pick a date."}), 400
    try:
        new = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "That date isn't valid."}), 400
    if new > date.today():
        return jsonify({"error": "That date is in the future."}), 400

    row        = db_query("SELECT last_period, cycle_len, period_len FROM users WHERE id = %s",
                          (current_user.id,), one=True)
    cycle_len  = row["cycle_len"] or 28
    period_len = row["period_len"] or 5
    last_str   = row["last_period"]

    archived = False
    duration = None

    # 2 ─ archive the cycle that just ended (if we had a reference date)
    if last_str:
        last = date.fromisoformat(str(last_str))
        if new <= last:
            return jsonify({
                "error": f"Your new period must start after the last one "
                         f"({last.strftime('%d %b %Y')})."
            }), 400
        duration = (new - last).days
        db_query(
            "INSERT INTO cycle_history (user_id, start_date, cycle_len, period_len) VALUES (%s, %s, %s, %s)",
            (current_user.id, str(last), duration, period_len), write=True,
        )
        archived = True

    # move the reference date to the new period start
    db_query("UPDATE users SET last_period = %s WHERE id = %s",
             (date_str, current_user.id), write=True)

    # 3 ─ learn: recompute cycle_len from the history average
    learned = _learned_cycle_len(current_user.id, cycle_len)
    if learned != cycle_len:
        db_query("UPDATE users SET cycle_len = %s WHERE id = %s",
                 (learned, current_user.id), write=True)

    # 4 ─ keep the alerting engine's mirror in sync
    sync_cycles_from_history(current_user.id, db_query)

    return jsonify({
        "ok":            True,
        "lastPeriod":    date_str,
        "cycleLen":      learned,
        "archived":      archived,
        "cycleDuration": duration,
    })


@history_bp.get("/cycle/history")
@login_required
def cycle_history():
    rows = db_query(
        "SELECT id, start_date, cycle_len, period_len FROM cycle_history "
        "WHERE user_id = %s ORDER BY start_date DESC",
        (current_user.id,),
    )
    return jsonify([{
        "id":        r["id"],
        "startDate": str(r["start_date"]),
        "cycleLen":  r["cycle_len"],
        "periodLen": r["period_len"],
    } for r in rows])


@history_bp.post("/cycle/history/add")
@login_required
def add_past_cycle():
    """Manually backfill a past cycle."""
    data       = request.json or {}
    start_date = data.get("startDate")

    if not start_date:
        return jsonify({"error": "Start date required"}), 400
    try:
        d = date.fromisoformat(start_date)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date"}), 400
    if d > date.today():
        return jsonify({"error": "That date is in the future."}), 400

    cycle_len  = _clamp(data.get("cycleLen", 28), MIN_CYCLE, MAX_CYCLE, 28)
    period_len = _clamp(data.get("periodLen", 5), MIN_PERIOD, MAX_PERIOD, 5)

    db_query(
        "INSERT INTO cycle_history (user_id, start_date, cycle_len, period_len) VALUES (%s, %s, %s, %s)",
        (current_user.id, start_date, cycle_len, period_len), write=True,
    )
    sync_cycles_from_history(current_user.id, db_query)
    return jsonify({"ok": True})


@history_bp.post("/cycle/history/update")
@login_required
def update_past_cycle():
    """Edit an existing cycle in the history."""
    data       = request.json or {}
    cycle_id   = data.get("id")
    start_date = data.get("startDate")
    if not cycle_id or not start_date:
        return jsonify({"error": "Missing cycle id or date"}), 400
    try:
        d = date.fromisoformat(start_date)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date"}), 400
    if d > date.today():
        return jsonify({"error": "That date is in the future."}), 400

    cycle_len  = _clamp(data.get("cycleLen", 28), MIN_CYCLE, MAX_CYCLE, 28)
    period_len = _clamp(data.get("periodLen", 5), MIN_PERIOD, MAX_PERIOD, 5)

    rows = db_query(
        "UPDATE cycle_history SET start_date = %s, cycle_len = %s, period_len = %s "
        "WHERE id = %s AND user_id = %s",
        (start_date, cycle_len, period_len, cycle_id, current_user.id), write=True,
    )
    if not rows:
        return jsonify({"error": "Cycle not found"}), 404
    sync_cycles_from_history(current_user.id, db_query)
    return jsonify({"ok": True})


@history_bp.post("/cycle/history/delete")
@login_required
def delete_past_cycle():
    """Remove a cycle from the history."""
    data     = request.json or {}
    cycle_id = data.get("id")
    if not cycle_id:
        return jsonify({"error": "Missing cycle id"}), 400
    db_query("DELETE FROM cycle_history WHERE id = %s AND user_id = %s",
             (cycle_id, current_user.id), write=True)
    sync_cycles_from_history(current_user.id, db_query)
    return jsonify({"ok": True})
