from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils.auth_decorators import require_role

from app.services.routing.route_engine import route_engine

patrol_bp = Blueprint("patrol", __name__)


@patrol_bp.post("/optimize")
@jwt_required()
@require_role('officer', 'admin')
def optimize_patrol():
    data = request.get_json(silent=True) or {}
    hotspot_ids = data.get("hotspot_ids", [])
    algorithm = data.get("algorithm", "both")
    results = route_engine.optimize(hotspot_ids, algorithm=algorithm)
    return jsonify({"routes": [route_engine._result_to_dict(r) for r in results]}), 200


@patrol_bp.post("/compare")
@jwt_required()
@require_role('officer', 'admin')
def compare_patrol_algorithms():
    data = request.get_json(silent=True) or {}
    return jsonify(route_engine.compare_algorithms(data.get("hotspot_ids", []))), 200
