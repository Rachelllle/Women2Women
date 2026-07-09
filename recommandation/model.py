import os, csv
import numpy as np
from sentence_transformers import SentenceTransformer, util

def _load_tips():
    csv_path = os.path.join(os.path.dirname(__file__), 'recommendations.csv')
    tips = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row['cycle_day_min'] = int(row['cycle_day_min'])
            row['cycle_day_max'] = int(row['cycle_day_max'])
            row['_text'] = f"{row['phase']} {row['kind']} {row['tag']} {row['title']} {row['body']}"
            tips.append(row)
    return tips

_tips       = _load_tips()
_model      = SentenceTransformer('all-MiniLM-L6-v2')
_embeddings = _model.encode([t['_text'] for t in _tips], convert_to_tensor=True)

CATEGORIES = ['food', 'move', 'mood', 'care']


def day_to_phase(day: int, cycle_len: int = 28) -> str:
    """Map a day-of-cycle to its menstrual phase."""
    if day <= 5:                  return "menstrual"
    if day <= cycle_len // 2:     return "follicular"
    if day <= cycle_len // 2 + 3: return "ovulation"
    return "luteal"


def get_recommendations(day: int, phase: str, feeling: str = '',
                        cycle_len: int = 28, period_len: int = 5) -> list[dict]:
    days_to_next = cycle_len - day
    query = (
        f"{phase} day {day} of {cycle_len} day cycle, "
        f"{days_to_next} days until next period, "
        f"period lasts {period_len} days"
    )
    if feeling:
        query += f", feeling {feeling}"

    query_vec = _model.encode(query, convert_to_tensor=True)
    scores    = util.cos_sim(query_vec, _embeddings).squeeze().cpu().numpy()

    result = []
    for category in CATEGORIES:
        eligible = [
            (i, t) for i, t in enumerate(_tips)
            if t['phase'] == phase
            and t['kind'] == category
            and t['cycle_day_min'] <= day <= t['cycle_day_max']
        ]
        if not eligible:
            eligible = [
                (i, t) for i, t in enumerate(_tips)
                if t['phase'] == phase and t['kind'] == category
            ]
        if not eligible:
            continue

        best_idx, best_tip = max(eligible, key=lambda x: scores[x[0]])
        result.append({
            'kind':  best_tip['kind'],
            'tag':   best_tip['tag'],
            'title': best_tip['title'],
            'body':  best_tip['body'],
        })

    return result
