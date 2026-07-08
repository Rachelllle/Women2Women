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