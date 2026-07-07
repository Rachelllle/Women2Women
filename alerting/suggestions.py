"""
Suggestion de symptômes à cocher, selon la phase du cycle et l'âge
de l'utilisatrice. S'appuie sur symptom_catalog_stats.
"""
from alerting.seed_from_kaggle import age_to_bracket


def get_symptom_suggestions(phase: str, age: int, db_query, top_n: int = 4) -> list[dict]:
    bracket = age_to_bracket(age)

    rows = db_query(
        """
        SELECT symptom_tag, occurrence_count, total_logs_in_bucket
        FROM symptom_catalog_stats
        WHERE phase = %s AND age_bracket = %s
        ORDER BY (occurrence_count / total_logs_in_bucket) DESC
        LIMIT %s
        """,
        (phase, bracket, top_n),
    )

    if not rows:
        return _default_fallback(phase)

    return [
        {
            "symptom": r["symptom_tag"],
            "frequency": round(r["occurrence_count"] / r["total_logs_in_bucket"], 3),
        }
        for r in rows
    ]


def _default_fallback(phase: str) -> list[dict]:
    defaults = {
        "menstrual":  ["Cramps", "Headache", "Fatigue"],
        "follicular": ["Fatigue"],
        "ovulation":  ["Bloating"],
        "luteal":     ["Bloating", "Mood Swings", "Fatigue"],
    }
    return [{"symptom": s, "frequency": None} for s in defaults.get(phase, [])]


if __name__ == "__main__":
    from database.db import db_query

    for phase in ["menstrual", "luteal"]:
        for age in [20, 30, 44]:
            result = get_symptom_suggestions(phase, age, db_query)
            print(f"{phase} / {age} ans -> {result}")