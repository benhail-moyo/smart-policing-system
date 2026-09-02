from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.models import Hotspot, HotspotHistory
from app.services.gis.hotspot_analysis import hotspot_service
from app.utils.auth_decorators import require_role

hotspots_bp = Blueprint("hotspots", __name__)


@hotspots_bp.post("/analyze")
@jwt_required(optional=True)
def analyze_hotspots():
    data = request.get_json(silent=True) or {}
    try:
        days_back = int(data.get("days_back", 30))
    except (TypeError, ValueError):
        days_back = 30

    result = hotspot_service.run_hotspot_analysis(days_back=days_back)
    # Filter out dormant hotspots from analysis response
    hotspots = db.session.query(Hotspot).filter(
        Hotspot.status.in_(['emerging', 'active', 'cooling'])
    ).order_by(Hotspot.risk_score.desc()).all()
    dicts = [h.to_dict() for h in hotspots]
    return jsonify({
        "analyzed": result.get("source_count", 0),
        "hotspots": dicts,
        "results": dicts,
        "hotspots_generated": result.get("hotspots_generated", len(dicts)),
    }), 200


@hotspots_bp.get("/")
@jwt_required(optional=True)
def list_hotspots():
    """List hotspots, excluding dormant by default."""
    include_dormant = request.args.get('include_dormant', 'false').lower() == 'true'
    
    query = db.session.query(Hotspot)
    if not include_dormant:
        query = query.filter(Hotspot.status.in_(['emerging', 'active', 'cooling']))
    
    hotspots = query.order_by(Hotspot.risk_score.desc()).all()
    dicts = [h.to_dict() for h in hotspots]
    return jsonify({"hotspots": dicts}), 200


@hotspots_bp.get("/all")
@jwt_required(optional=True)
def list_all_hotspots():
    """List all hotspots regardless of status."""
    hotspots = db.session.query(Hotspot).order_by(Hotspot.risk_score.desc()).all()
    dicts = [h.to_dict() for h in hotspots]
    return jsonify({"hotspots": dicts}), 200


@hotspots_bp.get("/<uuid:hotspot_id>")
@jwt_required(optional=True)
def get_hotspot(hotspot_id):
    """Get single hotspot with summary stats."""
    hotspot = db.session.query(Hotspot).filter(Hotspot.hotspot_id == hotspot_id).first()
    if not hotspot:
        return jsonify({"error": "Hotspot not found"}), 404
    
    # Calculate summary stats
    history_count = db.session.query(HotspotHistory).filter(
        HotspotHistory.hotspot_id == hotspot_id
    ).count()
    
    return jsonify({
        "hotspot": hotspot.to_dict(),
        "summary": {
            "total_runs_tracked": history_count,
            "first_detected_at": hotspot.first_detected_at.isoformat(),
            "last_matched_at": hotspot.last_matched_at.isoformat(),
            "current_streak": hotspot.consecutive_misses
        }
    }), 200


@hotspots_bp.get("/<uuid:hotspot_id>/history")
@jwt_required(optional=True)
def get_hotspot_history(hotspot_id):
    """Get full history time series for a hotspot."""
    history = db.session.query(HotspotHistory).filter(
        HotspotHistory.hotspot_id == hotspot_id
    ).order_by(HotspotHistory.run_timestamp.asc()).all()
    
    return jsonify({
        "history": [h.to_dict() for h in history]
    }), 200



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
