
import pandas as pd

CSV_PATH = "alerting/menstrual_cycle_dataset_with_factors.csv"

# Hypothèse de mapping symptôme -> phase (documentée, cf. rapport de projet)
SYMPTOM_TO_PHASE = {
    "Cramps":      "menstrual",
    "Headache":    "menstrual",
    "Bloating":    "luteal",
    "Mood Swings": "luteal",
    "Fatigue":     "luteal",
}


def age_to_bracket(age: int) -> str:
    """Tranches alignées sur les seuils cliniques ACOG/FIGO utilisés pour
    la détection d'irrégularité (variabilité de cycle acceptable diffère
    selon l'âge)."""
    if age <= 25:
        return "18-25"
    if age <= 35:
        return "26-35"
    if age <= 45:
        return "36-45"
    return "46+"


def build_catalog_stats(csv_path: str = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    df["phase"] = df["Symptoms"].map(SYMPTOM_TO_PHASE)
    df["age_bracket"] = df["Age"].apply(age_to_bracket)

    # occurrence_count : nb de fois où ce symptôme apparaît dans ce bucket
    occ = (
        df.groupby(["phase", "age_bracket", "Symptoms"])
        .size()
        .reset_index(name="occurrence_count")
        .rename(columns={"Symptoms": "symptom_tag"})
    )

    # total_logs_in_bucket : nb total de logs (tous symptômes confondus)
    # pour ce (phase, age_bracket), sert à calculer une fréquence relative
    totals = (
        df.groupby(["phase", "age_bracket"])
        .size()
        .reset_index(name="total_logs_in_bucket")
    )

    stats = occ.merge(totals, on=["phase", "age_bracket"])
    stats["frequency"] = stats["occurrence_count"] / stats["total_logs_in_bucket"]
    return stats.sort_values(["phase", "age_bracket", "frequency"], ascending=[True, True, False])


def insert_into_db(stats: pd.DataFrame, db_query):
    """db_query : réutilise la fonction existante de database/db.py,
    passée en paramètre pour ne pas créer de dépendance croisée directe."""
    for _, row in stats.iterrows():
        db_query(
            """
            INSERT INTO symptom_catalog_stats
                (phase, age_bracket, symptom_tag, occurrence_count, total_logs_in_bucket)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT(phase, age_bracket, symptom_tag) DO UPDATE SET
                occurrence_count = occurrence_count + excluded.occurrence_count,
                total_logs_in_bucket = total_logs_in_bucket + excluded.total_logs_in_bucket
            """,
            (row["phase"], row["age_bracket"], row["symptom_tag"],
             int(row["occurrence_count"]), int(row["total_logs_in_bucket"])),
            write=True,
        )


if __name__ == "__main__":
    from database.db import db_query

    stats = build_catalog_stats()
    print(stats.to_string(index=False))
    print(f"\n{len(stats)} lignes prêtes à être insérées dans symptom_catalog_stats.")

    insert_into_db(stats, db_query)
    print("Import terminé dans symptom_catalog_stats.")