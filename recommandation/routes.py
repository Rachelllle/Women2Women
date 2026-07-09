"""Recommendation routes — phase-aware daily recommendations."""
from flask import Blueprint, request, jsonify
from recommandation.model import get_recommendations, day_to_phase

rec_bp = Blueprint("recommandation", __name__, url_prefix="/api")


@rec_bp.get("/recommendations")
def recommendations():
    day        = int(request.args.get("day", 14))
    phase      = request.args.get("phase") or day_to_phase(day)
    feeling    = request.args.get("feeling", "")
    cycle_len  = int(request.args.get("cycleLen", 28))
    period_len = int(request.args.get("periodLen", 5))
    return jsonify(get_recommendations(day, phase, feeling, cycle_len, period_len))
