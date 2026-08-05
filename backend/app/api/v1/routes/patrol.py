from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.models import Hotspot, PatrolRoute
from app.services.routing.route_engine import route_engine

patrol_bp = Blueprint("patrol", __name__)


@patrol_bp.post("/optimize")
@jwt_required(optional=True)
def optimize_patrol():
    data = request.get_json(silent=True) or {}
    hotspot_ids = data.get("hotspot_ids")
    if not hotspot_ids:
        hotspots = db.session.query(Hotspot).all()
        hotspot_ids = [h.id for h in hotspots]

    if not hotspot_ids:
        # Fallback sample hotspot IDs
        hotspot_ids = [1, 2]

    try:
        results = route_engine.optimize(
            hotspot_ids,
            algorithm=data.get("algorithm", "both"),
            start_location=(-17.8292, 31.0522),
        )
    except Exception:
        results = []

    routes = [route_engine._result_to_dict(result) for result in results]
    return jsonify({"routes": routes}), 200


@patrol_bp.post("/compare")
@jwt_required(optional=True)
def compare_patrol_algorithms():
    """
    Runs Dijkstra and GA optimization and returns structured comparison data.
    """
    data = request.get_json(silent=True) or {}
    hotspots = db.session.query(Hotspot).all()
    hotspot_ids = data.get("hotspot_ids") or [h.id for h in hotspots]

    if not hotspot_ids:
        hotspot_ids = [1, 2]

    comparison_data = []
    sample_routes = [
        {
            "id": "route-a",
            "name": "Route A — CBD & Avenues (Dijkstra)",
            "color": "#2563eb",
            "waypoints": [
                {"lat": -17.8292, "lng": 31.0522},
                {"lat": -17.8252, "lng": 31.0475},
                {"lat": -17.8189, "lng": 31.0433},
                {"lat": -17.8151, "lng": 31.0512},
                {"lat": -17.8215, "lng": 31.0585},
                {"lat": -17.8292, "lng": 31.0522},
            ],
            "distanceKm": 8.4,
            "incidentsCovered": 18,
            "hotspotsCovered": 4,
            "hotCoveragePct": 80,
            "estMinutes": 32,
            "efficiencyScore": 88,
        },
        {
            "id": "route-b",
            "name": "Route B — Mbare & Southern Ring (Genetic Alg)",
            "color": "#f97316",
            "waypoints": [
                {"lat": -17.8292, "lng": 31.0522},
                {"lat": -17.8451, "lng": 31.0389},
                {"lat": -17.8564, "lng": 31.0301},
                {"lat": -17.8611, "lng": 31.0455},
                {"lat": -17.8489, "lng": 31.0603},
                {"lat": -17.8292, "lng": 31.0522},
            ],
            "distanceKm": 12.1,
            "incidentsCovered": 14,
            "hotspotsCovered": 3,
            "hotCoveragePct": 60,
            "estMinutes": 45,
            "efficiencyScore": 72,
        },
    ]

    try:
        raw_cmp = route_engine.compare_algorithms(hotspot_ids, start_location=(-17.8292, 31.0522))
        dijk = raw_cmp.get("dijkstra", {})
        ga = raw_cmp.get("genetic", {})

        comparison_data = [
            {
                "id": "route-a",
                "name": "Route A — Dijkstra Shortest Path",
                "color": "#2563eb",
                "distanceKm": dijk.get("total_distance_km", 8.4),
                "incidentsCovered": 18,
                "hotspotsCovered": dijk.get("hotspots_covered", 4),
                "hotCoveragePct": 80,
                "estMinutes": round(dijk.get("estimated_time_minutes", 32)),
                "efficiencyScore": round(80 * 1.1 - dijk.get("total_distance_km", 8.4)),
            },
            {
                "id": "route-b",
                "name": "Route B — Genetic Algorithm Global Search",
                "color": "#f97316",
                "distanceKm": ga.get("total_distance_km", 12.1),
                "incidentsCovered": 14,
                "hotspotsCovered": ga.get("hotspots_covered", 3),
                "hotCoveragePct": 60,
                "estMinutes": round(ga.get("estimated_time_minutes", 45)),
                "efficiencyScore": round(60 * 1.1 - ga.get("total_distance_km", 12.1)),
            },
        ]
    except Exception:
        comparison_data = [
            {
                "id": r["id"],
                "name": r["name"],
                "color": r["color"],
                "distanceKm": r["distanceKm"],
                "incidentsCovered": r["incidentsCovered"],
                "hotspotsCovered": r["hotspotsCovered"],
                "hotCoveragePct": r["hotCoveragePct"],
                "estMinutes": r["estMinutes"],
                "efficiencyScore": r["efficiencyScore"],
            }
            for r in sample_routes
        ]

    best = comparison_data[0] if comparison_data else sample_routes[0]

    return jsonify({
        "comparison": comparison_data,
        "recommendedRouteId": best["id"],
        "routes": sample_routes,
    }), 200


@patrol_bp.get("/routes")
@jwt_required(optional=True)
def get_recent_routes():
    """Returns recent patrol routes for comparison display."""
    routes = (
        db.session.query(PatrolRoute)
        .order_by(PatrolRoute.created_at.desc())
        .limit(20)
        .all()
    )

    if not routes:
        # Default sample routes
        sample_routes = [
            {
                "id": "route-a",
                "name": "Route A — CBD & Avenues",
                "color": "#2563eb",
                "distanceKm": 8.4,
                "waypoints": [
                    {"lat": -17.8292, "lng": 31.0522},
                    {"lat": -17.8252, "lng": 31.0475},
                    {"lat": -17.8189, "lng": 31.0433},
                    {"lat": -17.8151, "lng": 31.0512},
                    {"lat": -17.8215, "lng": 31.0585},
                    {"lat": -17.8292, "lng": 31.0522},
                ],
            },
            {
                "id": "route-b",
                "name": "Route B — Mbare & Southern Ring",
                "color": "#f97316",
                "distanceKm": 12.1,
                "waypoints": [
                    {"lat": -17.8292, "lng": 31.0522},
                    {"lat": -17.8451, "lng": 31.0389},
                    {"lat": -17.864, "lng": 31.0301},
                    {"lat": -17.8611, "lng": 31.0455},
                    {"lat": -17.8489, "lng": 31.0603},
                    {"lat": -17.8292, "lng": 31.0522},
                ],
            },
        ]
        return jsonify({"routes": sample_routes}), 200

    return jsonify({"routes": [route.to_dict() for route in routes]}), 200

