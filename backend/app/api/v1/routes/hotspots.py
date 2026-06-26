from flask import Blueprint

hotspots_bp = Blueprint("hotspots", __name__)


@hotspots_bp.post("/analyze")
def analyze_hotspots():
    return {"hotspots": [], "clusters": []}, 200


@hotspots_bp.get("/heatmap")
def heatmap():
    return {"heatmap": []}, 200
