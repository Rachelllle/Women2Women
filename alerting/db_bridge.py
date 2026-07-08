"""
Pont entre la DB et scoring.py.
"""
from datetime import date

from alerting.scoring import (
    predict_next_period,
    check_missed_or_late,
    check_irregularity_combined,
    check_abnormal_pain,
)


def get_user_age(user_id: int, db_query) -> int | None:
    row = db_query(
        "SELECT birth_date FROM alerting_profile WHERE user_id = %s",
        (user_id,), one=True,
    )
    if not row or not row["birth_date"]:
        return None
    today = date.today()
    bd = row["birth_date"]
    if not isinstance(bd, date):          # SQLite stores dates as TEXT
        bd = date.fromisoformat(str(bd))
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def get_user_cycles(user_id: int, db_query) -> list[dict]:
    rows = db_query(
        """
        SELECT start_date, cycle_len, period_len
        FROM cycles
        WHERE user_id = %s
        ORDER BY start_date ASC
        """,
        (user_id,),
    )
    # scoring.py does date arithmetic, so parse TEXT start_date -> date
    for r in rows or []:
        if r.get("start_date") and not isinstance(r["start_date"], date):
            r["start_date"] = date.fromisoformat(str(r["start_date"]))
    return rows or []


def get_user_pain_scores(user_id: int, db_query, limit: int = 12) -> list[int]:
    rows = db_query(
        """
        SELECT pain_score FROM symptom_logs
        WHERE user_id = %s AND pain_score IS NOT NULL
        ORDER BY log_date DESC
        LIMIT %s
        """,
        (user_id, limit),
    )
    scores = [r["pain_score"] for r in (rows or [])]
    return list(reversed(scores))


def sync_cycles_from_history(user_id: int, db_query):
    """Rebuild the alerting `cycles` mirror from the single source of truth:
    the user's cycle_history (completed cycles) + their current open cycle
    (users.last_period). Called after any add/edit/delete so the alerting
    engine always reflects the real data — no drift, no duplicates."""
    db_query("DELETE FROM cycles WHERE user_id = %s AND source = 'real_user'", (user_id,), write=True)

    hist = db_query(
        "SELECT start_date, cycle_len, period_len FROM cycle_history "
        "WHERE user_id = %s ORDER BY start_date ASC",
        (user_id,),
    )
    for h in hist or []:
        db_query(
            "INSERT INTO cycles (user_id, start_date, cycle_len, period_len, source) "
            "VALUES (%s, %s, %s, %s, 'real_user')",
            (user_id, str(h["start_date"]), h["cycle_len"], h.get("period_len")), write=True,
        )

    # the current, not-yet-completed cycle (open, cycle_len stays NULL)
    u = db_query("SELECT last_period, period_len FROM users WHERE id = %s", (user_id,), one=True)
    if u and u["last_period"]:
        db_query(
            "INSERT INTO cycles (user_id, start_date, period_len, source) VALUES (%s, %s, %s, 'real_user')",
            (user_id, str(u["last_period"]), u["period_len"]), write=True,
        )


def generate_alerts_for_user(user_id: int, db_query, declared_cycle_len: int = 28) -> list[dict]:
    alerts = []
    age = get_user_age(user_id, db_query)
    cycles = get_user_cycles(user_id, db_query)

    if cycles:
        predicted_date, confidence = predict_next_period(cycles, declared_cycle_len)
        last_cycle = cycles[-1]
        new_cycle_logged = last_cycle["cycle_len"] is not None
        alert = check_missed_or_late(
            last_cycle["start_date"], predicted_date, date.today(), new_cycle_logged
        )
        if alert:
            alerts.append(alert)

    if age is not None and len(cycles) >= 3:
        cycle_lengths = [c["cycle_len"] for c in cycles if c["cycle_len"]]
        period_lengths = [c["period_len"] for c in cycles if c["period_len"]]
        if len(cycle_lengths) >= 3:
            alert = check_irregularity_combined(cycle_lengths, age, period_lengths)
            if alert:
                alerts.append(alert)

    pain_scores = get_user_pain_scores(user_id, db_query)
    if pain_scores:
        alert = check_abnormal_pain(pain_scores)
        if alert:
            alerts.append(alert)

    return alerts