from flask import Blueprint, request

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.get("/")
def list_incidents():
    return {"incidents": []}, 200


@incidents_bp.post("/")
def create_incident():
    data = request.get_json(silent=True) or {}
    return {
        "message": "Incident submission scaffolded",
        "incident": data,
    }, 201
