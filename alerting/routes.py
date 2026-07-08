"""
Routes Flask du module alerting, isolées dans leur propre blueprint.
"""
from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from database.db import db_query
from alerting.suggestions import get_symptom_suggestions
from alerting.db_bridge import generate_alerts_for_user, get_user_age

alerting_bp = Blueprint("alerting", __name__, url_prefix="/api/alerting")


@alerting_bp.post("/cycle")
@login_required
def log_cycle():
    """Enregistre le début d'un nouveau cycle pour l'utilisatrice connectée."""
    data = request.json or {}
    start_date = data.get("startDate")
    period_len = data.get("periodLen")

    if not start_date:
        return jsonify({"error": "startDate requis"}), 400

    # Complète le cycle_len du cycle précédent maintenant qu'on connaît sa fin.
    # SQLite ne supporte ni DATEDIFF ni UPDATE ... ORDER BY LIMIT : on cible le
    # cycle ouvert le plus récent par son id et on calcule la durée en Python.
    prev = db_query(
        "SELECT id, start_date FROM cycles WHERE user_id = %s AND cycle_len IS NULL "
        "ORDER BY start_date DESC LIMIT 1",
        (current_user.id,), one=True,
    )
    if prev:
        try:
            clen = (date.fromisoformat(start_date) - date.fromisoformat(str(prev["start_date"]))).days
            if clen > 0:
                db_query("UPDATE cycles SET cycle_len = %s WHERE id = %s",
                         (clen, prev["id"]), write=True)
        except (ValueError, TypeError):
            pass

    db_query(
        "INSERT INTO cycles (user_id, start_date, period_len, source) VALUES (%s, %s, %s, 'real_user')",
        (current_user.id, start_date, period_len), write=True,
    )
    return jsonify({"ok": True}), 201


@alerting_bp.post("/symptom")
@login_required
def log_symptom():
    """Enregistre un ou plusieurs symptômes + douleur pour une date donnée."""
    data = request.json or {}
    log_date = data.get("date")
    phase = data.get("phase")
    pain_score = data.get("painScore")
    symptoms = data.get("symptoms", [])

    if not log_date:
        return jsonify({"error": "date requise"}), 400

    import json as json_lib
    db_query(
        """
        INSERT INTO symptom_logs (user_id, log_date, phase, pain_score, symptoms, source)
        VALUES (%s, %s, %s, %s, %s, 'real_user')
        """,
        (current_user.id, log_date, phase, pain_score, json_lib.dumps(symptoms)),
        write=True,
    )
    return jsonify({"ok": True}), 201


@alerting_bp.get("/suggestions")
@login_required
def suggestions():
    """Symptômes suggérés selon la phase actuelle et l'âge de l'utilisatrice."""
    phase = request.args.get("phase")
    if not phase:
        return jsonify({"error": "phase requise"}), 400

    age = get_user_age(current_user.id, db_query) or 28  # fallback neutre
    result = get_symptom_suggestions(phase, age, db_query)
    return jsonify(result)


@alerting_bp.post("/refresh")
@login_required
def refresh_alerts():
    """Génère les alertes à la demande pour l'utilisatrice connectée et les
    écrit dans alerts_log (même logique que le job WhatsApp, sans l'envoi).
    Permet d'afficher des alertes dans l'app sans dépendre du cron."""
    from alerting.db_bridge import generate_alerts_for_user
    from alerting.alerting_job import was_recently_logged, log_alert

    row = db_query("SELECT cycle_len FROM users WHERE id = %s", (current_user.id,), one=True)
    declared = (row and row["cycle_len"]) or 28

    generated = generate_alerts_for_user(current_user.id, db_query, declared)
    created = 0
    for alert in generated:
        # display-only dedup: don't mark as WhatsApp-sent, so the job can still push it
        if was_recently_logged(current_user.id, alert["type"]):
            continue
        log_alert(current_user.id, alert)   # whatsapp_sent defaults to 0
        created += 1
    return jsonify({"ok": True, "created": created})


@alerting_bp.get("/alerts")
@login_required
def alerts():
    """Historique réel des alertes envoyées (mêmes données que WhatsApp),
    pas un recalcul à la volée -> ce que l'utilisatrice voit dans l'app
    correspond exactement à ce qu'elle a reçu sur WhatsApp."""
    rows = db_query(
        """
        SELECT id, type, level, message_sent, sent_at, user_feedback
        FROM alerts_log
        WHERE user_id = %s
        ORDER BY sent_at DESC
        LIMIT 30
        """,
        (current_user.id,),
    )
    result = [
        {
            "id": r["id"],
            "type": r["type"],
            "level": r["level"],
            "message": r["message_sent"],
            "sentAt": str(r["sent_at"]),
            "feedback": r["user_feedback"],
        }
        for r in (rows or [])
    ]
    return jsonify(result)


@alerting_bp.post("/alerts/<int:alert_id>/feedback")
@login_required
def alert_feedback(alert_id):
    """Permet à l'utilisatrice de dire si une alerte lui a été utile ou non."""
    data = request.json or {}
    feedback = data.get("feedback")
    if feedback not in ("utile", "pas_pertinent"):
        return jsonify({"error": "feedback invalide"}), 400

    db_query(
        "UPDATE alerts_log SET user_feedback = %s WHERE id = %s AND user_id = %s",
        (feedback, alert_id, current_user.id), write=True,
    )
    return jsonify({"ok": True})


@alerting_bp.get("/profile")
@login_required
def get_alerting_profile():
    """Lit le profil alerting existant (pour préremplir le formulaire)."""
    row = db_query(
        "SELECT birth_date, phone_number, whatsapp_consent FROM alerting_profile WHERE user_id = %s",
        (current_user.id,), one=True,
    )
    if not row:
        return jsonify({"birthDate": None, "phoneNumber": None, "whatsappConsent": False})
    return jsonify({
        "birthDate": str(row["birth_date"]) if row["birth_date"] else None,
        "phoneNumber": row["phone_number"],
        "whatsappConsent": bool(row["whatsapp_consent"]),
    })


@alerting_bp.post("/profile")
@login_required
def save_alerting_profile():
    """Enregistre l'âge (date de naissance) et le consentement WhatsApp."""
    data = request.json or {}
    birth_date = data.get("birthDate")
    phone_number = data.get("phoneNumber")
    consent = bool(data.get("whatsappConsent", False))

    db_query(
        """
        INSERT INTO alerting_profile (user_id, birth_date, phone_number, whatsapp_consent)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(user_id) DO UPDATE SET
            birth_date = excluded.birth_date,
            phone_number = excluded.phone_number,
            whatsapp_consent = excluded.whatsapp_consent
        """,
        (current_user.id, birth_date, phone_number, int(consent)), write=True,
    )
    return jsonify({"ok": True})