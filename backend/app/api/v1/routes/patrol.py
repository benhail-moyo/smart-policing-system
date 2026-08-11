from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.models import Hotspot, PatrolRoute
from app.services.gis.hotspot_analysis import hotspot_service
from app.services.routing.route_engine import route_engine

patrol_bp = Blueprint("patrol", __name__)


def _route_inputs(requested_ids=None):
    """Resolve current route inputs from the persisted crime dataset."""
    hotspots = db.session.query(Hotspot).order_by(Hotspot.risk_score.desc()).all()
    if not hotspots:
        # Rebuild hotspot data from the current incidents before routing.
        hotspot_service.run_hotspot_analysis()
        hotspots = db.session.query(Hotspot).order_by(Hotspot.risk_score.desc()).all()

    if requested_ids:
        requested = {int(hotspot_id) for hotspot_id in requested_ids}
        hotspots = [hotspot for hotspot in hotspots if hotspot.id in requested]

    hotspots = [hotspot for hotspot in hotspots if hotspot.lat is not None and hotspot.lng is not None]
    if not hotspots:
        return [], None

    # The starting point follows the selected dataset rather than using a
    # hard-coded city coordinate.
    start_location = (
        sum(float(hotspot.lat) for hotspot in hotspots) / len(hotspots),
        sum(float(hotspot.lng) for hotspot in hotspots) / len(hotspots),
    )
    return [hotspot.id for hotspot in hotspots], start_location


def _comparison_row(result, route_id, color):
    hotspots = db.session.query(Hotspot).filter(Hotspot.id.in_(result.hotspot_ids)).all()
    incidents_covered = sum(hotspot.incident_count for hotspot in hotspots)
    return {
        "id": route_id,
        "name": f"{result.algorithm.title()} dataset route",
        "color": color,
        "distanceKm": result.total_distance_km,
        "incidentsCovered": incidents_covered,
        "hotspotsCovered": result.hotspots_covered,
        "hotCoveragePct": 100 if result.hotspots_covered else 0,
        "estMinutes": round(result.estimated_time_minutes),
        "efficiencyScore": round(
            (incidents_covered * 10 + result.hotspots_covered * 5)
            / max(result.total_distance_km, 0.1),
            1,
        ),
    }


@patrol_bp.post("/optimize")
@jwt_required(optional=True)
def optimize_patrol():
    data = request.get_json(silent=True) or {}
    hotspot_ids, start_location = _route_inputs(data.get("hotspot_ids"))
    if not hotspot_ids:
        return jsonify({"error": "No routable hotspots are available in the incident dataset"}), 422

    try:
        results = route_engine.optimize(
            hotspot_ids,
            algorithm=data.get("algorithm", "both"),
            start_location=start_location,
        )
    except Exception as exc:
        return jsonify({"error": f"Route generation failed: {exc}"}), 500

    return jsonify({"routes": [route_engine._result_to_dict(result) for result in results]}), 200


@patrol_bp.post("/compare")
@jwt_required(optional=True)
def compare_patrol_algorithms():
    """Generate both algorithm candidates from the live hotspot dataset."""
    data = request.get_json(silent=True) or {}
    hotspot_ids, start_location = _route_inputs(data.get("hotspot_ids"))
    if not hotspot_ids:
        return jsonify({"error": "No routable hotspots are available in the incident dataset"}), 422

    try:
        results = route_engine.optimize(hotspot_ids, algorithm="both", start_location=start_location)
    except Exception as exc:
        return jsonify({"error": f"Route comparison failed: {exc}"}), 500

    comparison = [
        _comparison_row(result, f"route-{result.algorithm}", "#2563eb" if result.algorithm == "dijkstra" else "#f97316")
        for result in results
    ]
    best = max(comparison, key=lambda route: route["efficiencyScore"])
    return jsonify({
        "comparison": comparison,
        "recommendedRouteId": best["id"],
        "routes": [route_engine._result_to_dict(result) for result in results],
    }), 200


@patrol_bp.post("/metrics")
@jwt_required(optional=True)
def route_metrics():
    data = request.get_json(silent=True) or {}
    waypoints = data.get("waypoints") or []
    if not isinstance(waypoints, list) or len(waypoints) < 2:
        return jsonify({"error": "Provide at least two waypoints"}), 400

    try:
        points = [(float(point["lat"]), float(point["lng"])) for point in waypoints]
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Each waypoint must contain numeric lat and lng"}), 400

    distance_km = route_engine._calculate_total_distance(points)
    return jsonify({
        "distanceKm": distance_km,
        "estMinutes": round(distance_km / route_engine.AVERAGE_SPEED_KMH * 60),
        "points": len(points),
    }), 200


@patrol_bp.get("/routes")
@jwt_required(optional=True)
def get_recent_routes():
    """Return generated route history; no sample routes are substituted."""
    routes = (
        db.session.query(PatrolRoute)
        .order_by(PatrolRoute.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify({"routes": [route.to_dict() for route in routes]}), 200
