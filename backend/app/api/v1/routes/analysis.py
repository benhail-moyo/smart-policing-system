from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services.analysis.report_service import analysis_report_service

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.post("/report")
@jwt_required(optional=True)
def generate_report():
    data = request.get_json(silent=True) or {}
    try:
        period_days = int(data.get("periodDays", 30))
    except (TypeError, ValueError):
        period_days = 30

    try:
        report = analysis_report_service.generate_report(period_days=period_days)
    except Exception as exc:
        return jsonify({"error": f"Analysis generation failed: {exc}"}), 500

    return jsonify({"report": report}), 200
