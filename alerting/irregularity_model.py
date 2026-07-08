"""
Détection d'irrégularité via Isolation Forest.
Usage : python -m alerting.irregularity_model
"""
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest_irregularity.joblib")
FEATURE_COLUMNS = ["cycle_len_mean", "cycle_len_std", "cycle_len_trend", "period_len_mean"]


def _trend_slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values, 1)
    return float(slope)


def build_features_from_kaggle(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    rows = []
    for user_id, group in df.groupby("User ID"):
        group = group.sort_values("Cycle Start Date")
        lengths = group["Cycle Length"].tolist()
        rows.append({
            "user_ref": f"seed_{user_id}",
            "cycle_len_mean": np.mean(lengths),
            "cycle_len_std": np.std(lengths),
            "cycle_len_trend": _trend_slope(lengths),
            "period_len_mean": group["Period Length"].mean(),
        })
    return pd.DataFrame(rows)


def build_features_for_user(cycles: list[dict]) -> dict | None:
    complete = [c for c in cycles if c.get("cycle_len") and c.get("period_len")]
    if len(complete) < 3:
        return None

    lengths = [c["cycle_len"] for c in complete]
    period_lengths = [c["period_len"] for c in complete]
    return {
        "cycle_len_mean": float(np.mean(lengths)),
        "cycle_len_std": float(np.std(lengths)),
        "cycle_len_trend": _trend_slope(lengths),
        "period_len_mean": float(np.mean(period_lengths)),
    }


def train_and_save(csv_path: str, contamination: float = 0.1) -> IsolationForest:
    features_df = build_features_from_kaggle(csv_path)
    X = features_df[FEATURE_COLUMNS].values

    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
    model.fit(X)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Modèle entraîné sur {len(features_df)} utilisatrices (seed), sauvegardé -> {MODEL_PATH}")
    return model


def load_model() -> IsolationForest:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "Modèle introuvable. Lance d'abord : python -m alerting.irregularity_model"
        )
    return joblib.load(MODEL_PATH)


def score_user(user_features: dict, model: IsolationForest = None) -> dict:
    if model is None:
        model = load_model()

    X = np.array([[user_features[col] for col in FEATURE_COLUMNS]])
    score_raw = float(model.decision_function(X)[0])
    is_anomaly = bool(model.predict(X)[0] == -1)

    return {"score_raw": round(score_raw, 3), "is_anomaly": is_anomaly}


if __name__ == "__main__":
    CSV_PATH = os.path.join(os.path.dirname(__file__), "menstrual_cycle_dataset_with_factors.csv")
    model = train_and_save(CSV_PATH)

    print("\n=== Test sur des profils fictifs ===")
    regular_user = {"cycle_len_mean": 37, "cycle_len_std": 2, "cycle_len_trend": 0.1, "period_len_mean": 5}
    print("Régulière :", score_user(regular_user, model))

    atypical_user = {"cycle_len_mean": 21, "cycle_len_std": 0.5, "cycle_len_trend": -3.0, "period_len_mean": 8}
    print("Atypique  :", score_user(atypical_user, model))