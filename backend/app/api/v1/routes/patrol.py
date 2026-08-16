from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.models import Hotspot, PatrolRoute
from app.services.gis.hotspot_analysis import hotspot_service
from app.services.routing.route_engine import route_engine
from app.utils.auth_decorators import require_role

patrol_bp = Blueprint("patrol", __name__)


def _resolve_route_inputs(requested_ids=None):
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


def _resolve_comparison_hotspots(requested_ids=None):
    """Return the current critical hotspots and a central patrol start point."""
    hotspots = db.session.query(Hotspot).order_by(Hotspot.risk_score.desc()).all()
    if not hotspots:
        hotspot_service.run_hotspot_analysis()
        hotspots = db.session.query(Hotspot).order_by(Hotspot.risk_score.desc()).all()

    hotspots = [hotspot for hotspot in hotspots if hotspot.lat is not None and hotspot.lng is not None]
    if requested_ids:
        requested = {int(hotspot_id) for hotspot_id in requested_ids}
        hotspots = [hotspot for hotspot in hotspots if hotspot.id in requested]
    else:
        critical_hotspots = [hotspot for hotspot in hotspots if hotspot.risk_score >= 0.6]
        # A comparison needs a meaningful multi-stop route. If there are fewer
        # than three critical clusters, include the next highest-risk hotspots.
        if len(critical_hotspots) >= 3:
            hotspots = critical_hotspots

    if len(hotspots) < 3:
        return [], None

    start_location = (
        sum(float(hotspot.lat) for hotspot in hotspots) / len(hotspots),
        sum(float(hotspot.lng) for hotspot in hotspots) / len(hotspots),
    )
    return hotspots, start_location


def _road_comparison_route(result, route_id, name, color, hotspots):
    """Format road-network results for the map and comparison table."""
    hotspot_order = []
    if hotspots:
        for point_index in result["order"]:
            if point_index == 0:
                continue  # Index zero is the patrol start, not a hotspot.
            hotspot = hotspots[point_index - 1]
            hotspot_order.append({
                "id": hotspot.id,
                "lat": hotspot.lat,
                "lng": hotspot.lng,
                "level": "critical" if hotspot.risk_score >= 0.6 else "high",
                "riskScore": round(float(hotspot.risk_score), 2),
                "incidentCount": hotspot.incident_count,
            })

    hotspot_ids = list(dict.fromkeys(item["id"] for item in hotspot_order))
    incidents_covered = sum(hotspot.incident_count for hotspot in hotspots if hotspot.id in hotspot_ids)
    distance_km = result["total_distance_m"] / 1000
    return {
        "id": route_id,
        "name": name,
        "color": color,
        "algorithm": result["algorithm"],
        "distanceKm": round(distance_km, 2),
        "hotspotsCovered": len(hotspot_ids),
        "hotCoveragePct": round(len(hotspot_ids) / len(hotspots) * 100) if hotspots else 0,
        "incidentsCovered": incidents_covered,
        "estMinutes": round(distance_km / 40 * 60),
        "efficiencyScore": round((incidents_covered * 10 + len(hotspot_ids) * 5) / max(distance_km, 0.1), 1),
        "geometry": result["geometry"],
        "waypoints": [],
        "hotspotIds": hotspot_ids,
        "hotspotOrder": hotspot_order,
    }


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
    hotspot_ids, start_location = _resolve_route_inputs(data.get("hotspot_ids"))
    if not hotspot_ids:
        return jsonify({"error": "No routable hotspots are available in the incident dataset"}), 422

    try:
        # Use original hotspot-based routing (straight lines)
        # Set save_to_db=False to avoid duplicate routes
        results = route_engine.optimize(
            hotspot_ids,
            algorithm=data.get("algorithm", "both"),
            start_location=start_location,
            save_to_db=False
        )
        return jsonify({"routes": [route_engine._result_to_dict(result) for result in results]}), 200
            
    except Exception as exc:
        return jsonify({"error": f"Route generation failed: {exc}"}), 500


@patrol_bp.post("/compare")
@jwt_required(optional=True)
def compare_patrol_algorithms():
    """
    Generate both algorithm candidates from the live hotspot dataset.
    Extends existing comparison with road network comparison when provided.
    """
    data = request.get_json(silent=True) or {}
    
    # Run the road-network comparison for either explicit points or the
    # automatically selected current critical hotspots.
    try:
        if "start" in data and "stops" in data:
            route_data = data
            hotspots = []
        else:
            hotspots, start_location = _resolve_comparison_hotspots(data.get("hotspot_ids"))
            if not hotspots:
                return jsonify({"error": "At least three routable hotspots are required for comparison"}), 422
            route_data = {
                "city": "harare",
                "start": {"lat": start_location[0], "lng": start_location[1]},
                "stops": [{"lat": hotspot.lat, "lng": hotspot.lng} for hotspot in hotspots],
            }

        from app.services.routing.route_service import get_route_service
        service = get_route_service()
        request_obj = service.validate_multi_stop_request(route_data)
        road_comparison = service.compute_multi_stop_comparison(request_obj)
            
        baseline_route = _road_comparison_route(
            road_comparison["baseline"], "baseline", "Dijkstra Nearest-Neighbour", "#2563eb", hotspots
        )
        genetic_route = _road_comparison_route(
            road_comparison["genetic"], "genetic", "Genetic Algorithm", "#f97316", hotspots
        )
        routes = [baseline_route, genetic_route]
        best = max(routes, key=lambda route: route["efficiencyScore"])
        return jsonify({
            "comparison": routes,
            "recommendedRouteId": best["id"],
            "routes": routes,
            "hotspots": [hotspot.to_dict() for hotspot in hotspots],
            "road_network_comparison": road_comparison,
        }), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 422
    except RuntimeError as re:
        return jsonify({"error": str(re)}), 503
    except Exception as exc:
        return jsonify({"error": f"Road network comparison failed: {exc}"}), 500


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


@patrol_bp.post("/save")
@jwt_required()
@require_role("officer", "admin")
def save_route():
    """Explicitly save a route to the database."""
    data = request.get_json(silent=True) or {}
    
    try:
        route = PatrolRoute(
            algorithm=data.get("algorithm", "dijkstra"),
            waypoints=data.get("waypoints", []),
            total_distance_km=data.get("total_distance_km", 0),
            estimated_fuel_litres=data.get("estimated_fuel_litres", 0),
            estimated_time_minutes=data.get("estimated_time_minutes", 0),
            hotspots_covered=data.get("hotspots_covered", 0),
            computation_time_ms=data.get("computation_time_ms", 0),
            hotspot_ids=data.get("hotspot_ids", []),
        )
        db.session.add(route)
        db.session.commit()
        
        return jsonify({"message": "Route saved successfully", "route_id": route.id}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to save route: {exc}"}), 500


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


@patrol_bp.get("/status")
@jwt_required()
@require_role("officer", "admin")
def get_graph_status():
    """Return road network graph status without exposing internals."""
    try:
        from app.services.routing.graph_store import graph_store
        status = graph_store.get_status()
        return jsonify(status), 200
    except Exception as exc:
        return jsonify({"error": f"Failed to get graph status: {exc}"}), 500


@patrol_bp.post("/routes")
@jwt_required()
@require_role("officer", "admin")
def generate_point_to_point_route():
    """Generate point-to-point route using road network Dijkstra."""
    try:
        from app.services.routing.route_service import get_route_service
        service = get_route_service()
        data = request.get_json(silent=True) or {}
        request_obj = service.validate_point_to_point_request(data)
        result = service.compute_point_to_point_route(request_obj)
        
        return jsonify({
            "algorithm": result.algorithm,
            "total_distance_m": result.total_distance_m,
            "nodes_visited": result.nodes_visited,
            "execution_time_ms": result.execution_time_ms,
            "start_snap_distance_m": result.start_snap_distance_m,
            "end_snap_distance_m": result.end_snap_distance_m,
            "geometry": result.geometry
        }), 200
        
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 422
    except RuntimeError as re:
        return jsonify({"error": str(re)}), 503
    except Exception as exc:
        return jsonify({"error": f"Route generation failed: {exc}"}), 500
