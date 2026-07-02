from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils.auth_decorators import require_role

hotspots_bp = Blueprint("hotspots", __name__)


@hotspots_bp.post("/analyze")
@jwt_required()
@require_role('officer', 'admin')
def analyze_hotspots():
    return jsonify({"hotspots": [], "clusters": []}), 200


@hotspots_bp.get("/heatmap")
def heatmap():
    return jsonify({"heatmap": []}), 200
