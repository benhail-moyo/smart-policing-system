from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.models import Hotspot
from app.services.gis.hotspot_analysis import hotspot_service
from app.utils.auth_decorators import require_role

hotspots_bp = Blueprint("hotspots", __name__)


@hotspots_bp.post("/analyze")
@jwt_required()
@require_role("officer", "admin")
def analyze_hotspots():
    data = request.get_json(silent=True) or {}
    try:
        days_back = int(data.get("days_back", 30))
    except (TypeError, ValueError):
        return jsonify({"error": "days_back must be an integer"}), 400

    if days_back < 1 or days_back > 3650:
        return jsonify({"error": "days_back must be between 1 and 3650"}), 400

    result = hotspot_service.run_hotspot_analysis(days_back=days_back)
    return jsonify(result), 200


@hotspots_bp.get("/")
@jwt_required()
def list_hotspots():
    hotspots = db.session.query(Hotspot).order_by(Hotspot.risk_score.desc()).all()
    return jsonify([hotspot.to_dict() for hotspot in hotspots]), 200


@hotspots_bp.get("/heatmap")
@jwt_required()
def heatmap():
    required = ("min_lng", "min_lat", "max_lng", "max_lat")
    missing = [name for name in required if request.args.get(name) is None]
    if missing:
        return jsonify({"error": f"Missing query parameters: {', '.join(missing)}"}), 400

    try:
        min_lng = float(request.args["min_lng"])
        min_lat = float(request.args["min_lat"])
        max_lng = float(request.args["max_lng"])
        max_lat = float(request.args["max_lat"])
        resolution = int(request.args.get("resolution", 50))
        days_back = int(request.args.get("days_back", 90))
    except (TypeError, ValueError):
        return jsonify({"error": "bbox, resolution, and days_back must be numeric"}), 400

    if min_lng >= max_lng or min_lat >= max_lat:
        return jsonify({"error": "Invalid bounding box"}), 400

    result = hotspot_service.generate_kde_heatmap(
        bbox=(min_lng, min_lat, max_lng, max_lat),
        resolution=resolution,
        days_back=days_back,
    )
    return jsonify(result), 200
