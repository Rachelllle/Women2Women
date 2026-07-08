"""
Logique de scoring pour le module alerting.
Fonctions pures, testables sans DB. Les 3 types d'alertes :
  - missed_log / late_period : retard ou oubli de saisie
  - irregularity              : variabilité de cycle (rule-based + ML)
  - abnormal_pain             : douleur au-dessus de la norme perso

Paliers : info / attention / recommandation
"""
from datetime import date
from statistics import mean, pstdev

IRREGULARITY_THRESHOLD_BY_AGE = {
    "18-25": 9,
    "26-41": 7,
    "42-45": 9,
}


def age_to_clinical_bracket(age: int) -> str:
    if age <= 25:
        return "18-25"
    if age <= 41:
        return "26-41"
    return "42-45"


def predict_next_period(cycles: list[dict], declared_cycle_len: int = 28) -> tuple[date, float]:
    if not cycles:
        return None, 0.0

    last_start = cycles[-1]["start_date"]
    known_lengths = [c["cycle_len"] for c in cycles if c["cycle_len"]]

    if len(known_lengths) < 2:
        avg_len = declared_cycle_len
        confidence = 0.4
    else:
        recent = known_lengths[-6:]
        avg_len = mean(recent)
        confidence = min(0.5 + 0.08 * len(recent), 0.9)

    predicted_date = last_start + __import__("datetime").timedelta(days=round(avg_len))
    return predicted_date, round(confidence, 2)


def check_missed_or_late(last_start: date, predicted_date: date, today: date,
                          new_cycle_logged: bool, delay_threshold_days: int = 5) -> dict | None:
    days_late = (today - predicted_date).days
    if days_late < delay_threshold_days:
        return None

    if new_cycle_logged:
        return {
            "type": "late_period",
            "level": "attention",
            "message": (
                "On a remarqué que ton cycle a été un peu plus long que prévu ce mois-ci. "
                "Rien d'alarmant en soi, ça arrive régulièrement. On continue de suivre."
            ),
        }
    else:
        return {
            "type": "missed_log",
            "level": "info",
            "message": (
                "Petit rappel : as-tu pensé à enregistrer le début de tes dernières règles ? "
                "Si elles n'ont pas encore commencé, ce n'est pas grave, on garde un œil dessus."
            ),
        }


def check_irregularity(cycle_lengths: list[int], age: int) -> dict | None:
    if len(cycle_lengths) < 3:
        return None

    window = cycle_lengths[-6:]
    diff = max(window) - min(window)
    threshold = IRREGULARITY_THRESHOLD_BY_AGE[age_to_clinical_bracket(age)]

    if diff < threshold - 3:
        return None

    if diff < threshold:
        return {
            "type": "irregularity",
            "level": "info",
            "message": (
                "Tes derniers cycles montrent une légère variation de durée. "
                "C'est courant et pas forcément préoccupant, on continue de suivre."
            ),
        }

    previous_window = cycle_lengths[-7:-1] if len(cycle_lengths) >= 7 else None
    persistent = False
    if previous_window and len(previous_window) >= 3:
        prev_diff = max(previous_window) - min(previous_window)
        persistent = prev_diff >= threshold

    if persistent:
        return {
            "type": "irregularity",
            "level": "recommandation",
            "message": (
                "Sur plusieurs mois de suivi, on observe une variation de cycle plus "
                "importante que la moyenne pour ton profil. Ce n'est pas un diagnostic : "
                "l'app détecte un écart statistique, pas une pathologie. Mais si ça persiste, "
                "ça peut valoir le coup d'en parler à un professionnel de santé."
            ),
        }
    else:
        return {
            "type": "irregularity",
            "level": "attention",
            "message": (
                "Tes derniers cycles ont été plus variables que d'habitude. "
                "On va continuer à suivre ça sur les prochains mois pour voir si "
                "c'est un pattern qui s'installe ou juste un mois particulier."
            ),
        }


def check_irregularity_combined(cycle_lengths: list[int], age: int,
                                 period_lengths: list[int] = None) -> dict | None:
    rule_alert = check_irregularity(cycle_lengths, age)
    ml_result = None

    if period_lengths and len(cycle_lengths) >= 3:
        try:
            from alerting.irregularity_model import build_features_for_user, score_user
            cycles_for_features = [
                {"cycle_len": cl, "period_len": pl}
                for cl, pl in zip(cycle_lengths, period_lengths)
            ]
            features = build_features_for_user(cycles_for_features)
            if features:
                ml_result = score_user(features)
        except FileNotFoundError:
            ml_result = None

    return _combine_irregularity_signals(rule_alert, ml_result)


def _combine_irregularity_signals(rule_alert: dict | None, ml_result: dict | None) -> dict | None:
    if ml_result is None:
        return rule_alert

    if rule_alert is None:
        if ml_result["is_anomaly"] and ml_result["score_raw"] < -0.1:
            return {
                "type": "irregularity",
                "level": "info",
                "message": (
                    "Le modèle a repéré un profil de cycle un peu atypique par rapport "
                    "à l'ensemble des utilisatrices suivies, sans que ça sorte de ta "
                    "propre normalité. On garde un œil dessus, rien à faire de particulier "
                    "pour l'instant."
                ),
                "ml_score": ml_result["score_raw"],
            }
        return None

    rule_alert = dict(rule_alert)
    rule_alert["ml_score"] = ml_result["score_raw"]

    if rule_alert["level"] == "attention" and ml_result["is_anomaly"]:
        rule_alert["level"] = "recommandation"
        rule_alert["message"] += (
            " Ce signal est aussi confirmé par la comparaison à l'ensemble des profils "
            "suivis, ce qui renforce l'intérêt d'en parler à un professionnel de santé."
        )

    return rule_alert


def check_abnormal_pain(pain_scores: list[int]) -> dict | None:
    if len(pain_scores) < 4:
        return None

    baseline = pain_scores[:-1]
    latest = pain_scores[-1]

    mu, sigma = mean(baseline), pstdev(baseline)
    if sigma == 0:
        sigma = 0.5

    z = (latest - mu) / sigma
    recent_high = len(pain_scores) >= 2 and pain_scores[-1] >= 7 and pain_scores[-2] >= 7

    if z < 1.5:
        return None
    elif z < 2.5 and not recent_high:
        return {
            "type": "abnormal_pain",
            "level": "attention",
            "message": (
                "Tu as signalé une douleur plus intense que d'habitude récemment. "
                "On continue de suivre ça — si ça se reproduit, pense à noter le contexte "
                "(intensité, durée) pour ton médecin le cas échéant."
            ),
        }
    else:
        return {
            "type": "abnormal_pain",
            "level": "recommandation",
            "message": (
                "Tu as signalé une douleur nettement plus intense que ta moyenne habituelle, "
                "et de façon répétée. On ne peut pas évaluer la cause depuis l'app, mais "
                "on te recommande d'en parler à un professionnel de santé."
            ),
        }


if __name__ == "__main__":
    print("=== Cas 1 : retard non enregistré ===")
    today = date(2026, 7, 7)
    cycles = [
        {"start_date": date(2026, 4, 1), "cycle_len": 28},
        {"start_date": date(2026, 4, 29), "cycle_len": 27},
        {"start_date": date(2026, 5, 26), "cycle_len": None},
    ]
    predicted, conf = predict_next_period(cycles)
    print(f"Prédiction : {predicted} (confiance {conf})")
    alert = check_missed_or_late(cycles[-1]["start_date"], predicted, today, new_cycle_logged=False)
    print(alert)

    print("\n=== Cas 2 : cycles réguliers ===")
    print(check_irregularity([28, 29, 27, 28, 30, 28], age=28))

    print("\n=== Cas 3 : cycles irréguliers persistants ===")
    print(check_irregularity([24, 38, 26, 40, 25, 41, 27], age=28))

    print("\n=== Cas 4 : douleur normale ===")
    print(check_abnormal_pain([4, 5, 4, 3, 5, 4]))

    print("\n=== Cas 5 : douleur anormale répétée ===")
    print(check_abnormal_pain([4, 5, 4, 3, 8, 9]))

    print("\n=== Cas 6 : rule-based + ML confirme -> recommandation ===")
    print(check_irregularity_combined([24, 38, 26, 39, 25, 40], age=28, period_lengths=[8]*6))

    print("\n=== Cas 7 : ML seul détecte un signal faible ===")
    print(check_irregularity_combined([21, 21, 22, 21, 22, 21], age=28, period_lengths=[8]*6))