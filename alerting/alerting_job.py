"""
Job planifié (à lancer 1x/jour, en local pour l'instant, puis en Lambda AWS
plus tard). Boucle sur les utilisatrices ayant consenti au WhatsApp,
calcule leurs alertes, évite les doublons récents, écrit dans alerts_log
et envoie le message.

Usage : python -m alerting.alerting_job

Nécessite un fichier .env à la racine du projet (jamais commité) avec :
    TWILIO_ACCOUNT_SID=...
    TWILIO_AUTH_TOKEN=...
    TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from database.db import db_query
from alerting.db_bridge import generate_alerts_for_user

load_dotenv()  # charge les variables du fichier .env

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")

# Ne pas renvoyer la même alerte (même type) à moins de X jours d'intervalle,
# pour éviter de spammer si le job tourne plusieurs fois ou si l'alerte reste
# active plusieurs jours de suite.
COOLDOWN_DAYS = {
    "missed_log": 1,
    "late_period": 2,
    "irregularity": 7,
    "abnormal_pain": 3,
}


def send_whatsapp(phone_number: str, message: str) -> bool:
    """
    Envoie un message WhatsApp via Twilio (mode sandbox).
    Si les credentials Twilio ne sont pas configurés (.env absent ou
    incomplet), retombe automatiquement sur une simulation console.
    """
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_FROM):
        print(f"[SIMULATION WHATSAPP — .env non configuré] -> {phone_number} : {message}")
        return True

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{phone_number}",
            body=message,
        )
        print(f"[WHATSAPP ENVOYÉ] -> {phone_number}")
        return True
    except Exception as e:
        print(f"[ERREUR ENVOI WHATSAPP] -> {phone_number} : {e}")
        return False


def get_consenting_users() -> list[dict]:
    """Utilisatrices ayant activé le consentement WhatsApp."""
    rows = db_query(
        """
        SELECT u.id AS user_id, ap.phone_number
        FROM users u
        JOIN alerting_profile ap ON ap.user_id = u.id
        WHERE ap.whatsapp_consent = 1 AND ap.phone_number IS NOT NULL
        """
    )
    return rows or []


def _cutoff(alert_type: str) -> str:
    cooldown = COOLDOWN_DAYS.get(alert_type, 3)
    return (datetime.now() - timedelta(days=cooldown)).strftime("%Y-%m-%d %H:%M:%S")


def log_alert(user_id: int, alert: dict, whatsapp_sent: int = 0):
    """Record an alert for display in the app. whatsapp_sent stays 0 unless it
    was actually pushed to WhatsApp by the job."""
    db_query(
        """
        INSERT INTO alerts_log (user_id, type, level, score, message_sent, whatsapp_sent)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, alert["type"], alert["level"], alert.get("ml_score"), alert["message"], whatsapp_sent),
        write=True,
    )


def was_recently_logged(user_id: int, alert_type: str) -> bool:
    """Any alert of this type recently recorded (used by the app to avoid
    piling up duplicate display rows each time the Alerts page opens)."""
    row = db_query(
        "SELECT id FROM alerts_log WHERE user_id = %s AND type = %s AND sent_at >= %s "
        "ORDER BY sent_at DESC LIMIT 1",
        (user_id, alert_type, _cutoff(alert_type)), one=True,
    )
    return row is not None


def was_recently_whatsapped(user_id: int, alert_type: str) -> bool:
    """Only real WhatsApp sends block the job — an alert merely shown in the app
    (whatsapp_sent = 0) does not prevent it from being pushed to WhatsApp."""
    row = db_query(
        "SELECT id FROM alerts_log WHERE user_id = %s AND type = %s AND whatsapp_sent = 1 "
        "AND sent_at >= %s ORDER BY sent_at DESC LIMIT 1",
        (user_id, alert_type, _cutoff(alert_type)), one=True,
    )
    return row is not None


def mark_whatsapp_sent(user_id: int, alert: dict):
    """Flag an existing recent display row as sent on WhatsApp, or insert one —
    so the app never shows a duplicate for the same alert."""
    row = db_query(
        "SELECT id FROM alerts_log WHERE user_id = %s AND type = %s AND sent_at >= %s "
        "ORDER BY sent_at DESC LIMIT 1",
        (user_id, alert["type"], _cutoff(alert["type"])), one=True,
    )
    if row:
        db_query("UPDATE alerts_log SET whatsapp_sent = 1 WHERE id = %s", (row["id"],), write=True)
    else:
        log_alert(user_id, alert, whatsapp_sent=1)


def run():
    users = get_consenting_users()
    print(f"{len(users)} utilisatrice(s) avec consentement WhatsApp actif.")

    total_sent = 0
    for user in users:
        user_id = user["user_id"]
        alerts = generate_alerts_for_user(user_id, db_query)

        for alert in alerts:
            if was_recently_whatsapped(user_id, alert["type"]):
                continue  # déjà ENVOYÉE sur WhatsApp récemment, on n'insiste pas

            sent_ok = send_whatsapp(user["phone_number"], alert["message"])
            if sent_ok:
                mark_whatsapp_sent(user_id, alert)
                total_sent += 1

    print(f"Job terminé : {total_sent} alerte(s) envoyée(s).")


if __name__ == "__main__":
    run()