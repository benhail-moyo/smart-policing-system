from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.models import PatrolRoute
from app.services.routing.route_engine import route_engine
from app.utils.auth_decorators import require_role

patrol_bp = Blueprint("patrol", __name__)


@patrol_bp.post("/optimize")
@jwt_required()
@require_role("officer", "admin")
def optimize_patrol():
    data = request.get_json(silent=True) or {}
    parsed = _parse_optimization_request(data)
    if parsed[1] is not None:
        return parsed[1]

    hotspot_ids, algorithm, start_location = parsed[0]
    try:
        results = route_engine.optimize(
            hotspot_ids,
            algorithm=algorithm,
            start_location=start_location,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"routes": [route_engine._result_to_dict(result) for result in results]}), 200


@patrol_bp.post("/compare")
@jwt_required()
@require_role("officer", "admin")
def compare_patrol_algorithms():
    """
    Academic endpoint: runs Dijkstra and GA on the same hotspot set.
    Response maps directly to the Chapter 4 comparison table.
    """
    data = request.get_json(silent=True) or {}
    parsed = _parse_optimization_request({**data, "algorithm": "both"})
    if parsed[1] is not None:
        return parsed[1]

    hotspot_ids, _, start_location = parsed[0]
    try:
        result = route_engine.compare_algorithms(hotspot_ids, start_location=start_location)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result), 200


@patrol_bp.get("/routes")
@jwt_required()
def get_recent_routes():
    """Returns recent patrol routes for comparison display."""
    routes = (
        db.session.query(PatrolRoute)
        .order_by(PatrolRoute.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify([
        {
            "id": route.id,
            "algorithm": route.algorithm,
            "created_at": route.created_at.isoformat() if route.created_at else None,
            "total_distance_km": route.total_distance_km,
            "estimated_fuel_litres": route.estimated_fuel_litres,
            "estimated_time_minutes": route.estimated_time_minutes,
            "hotspots_covered": route.hotspots_covered,
            "computation_time_ms": route.computation_time_ms,
            "hotspot_ids": route.hotspot_ids,
        }
        for route in routes
    ]), 200


def _parse_optimization_request(data):
    hotspot_ids = data.get("hotspot_ids", [])
    if not isinstance(hotspot_ids, list) or not hotspot_ids:
        return None, (jsonify({"error": "hotspot_ids must be a non-empty list"}), 400)

    try:
        hotspot_ids = [int(hotspot_id) for hotspot_id in hotspot_ids]
    except (TypeError, ValueError):
        return None, (jsonify({"error": "hotspot_ids must contain integers"}), 400)

    algorithm = str(data.get("algorithm", "both")).lower()
    if algorithm not in ("dijkstra", "genetic", "both"):
        return None, (jsonify({"error": "algorithm must be one of: dijkstra, genetic, both"}), 400)

    start_location = None
    has_start_lat = data.get("start_lat") is not None
    has_start_lng = data.get("start_lng") is not None
    if has_start_lat or has_start_lng:
        if not (has_start_lat and has_start_lng):
            return None, (jsonify({"error": "start_lat and start_lng must be provided together"}), 400)
        try:
            start_location = (float(data["start_lat"]), float(data["start_lng"]))
        except (TypeError, ValueError):
            return None, (jsonify({"error": "start_lat and start_lng must be numeric"}), 400)

    return (hotspot_ids, algorithm, start_location), None
