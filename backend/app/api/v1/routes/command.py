from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.models import Deployment, StrategicPlan, OfficerDailyLog
from app.utils.auth_decorators import require_role

command_bp = Blueprint("command", __name__)


def _user_id():
    return int(get_jwt_identity())


@command_bp.get("/deployments")
@jwt_required()
@require_role("admin")
def list_deployments():
    return jsonify({"deployments": [x.to_dict() for x in Deployment.query.order_by(Deployment.created_at.desc()).all()]})


@command_bp.post("/deployments")
@jwt_required()
@require_role("admin")
def create_deployment():
    data = request.get_json(silent=True) or {}
    if data.get("unitType") not in ("foot", "vehicle") or not data.get("areaName"):
        return jsonify({"error": "unitType and areaName are required"}), 400
    try:
        item = Deployment(unit_type=data["unitType"], area_name=data["areaName"].strip(), lat=float(data["lat"]), lng=float(data["lng"]), instructions=(data.get("instructions") or "").strip(), created_by_id=_user_id())
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "A valid map location is required"}), 400
    db.session.add(item); db.session.commit()
    return jsonify({"deployment": item.to_dict()}), 201


@command_bp.get("/plans")
@jwt_required()
@require_role("admin")
def list_plans():
    return jsonify({"plans": [x.to_dict() for x in StrategicPlan.query.order_by(StrategicPlan.created_at.desc()).all()]})


@command_bp.post("/plans")
@jwt_required()
@require_role("admin")
def create_plan():
    data = request.get_json(silent=True) or {}
    if not all(data.get(k) for k in ("title", "type", "areaName")):
        return jsonify({"error": "title, type and areaName are required"}), 400
    item = StrategicPlan(title=data["title"].strip(), plan_type=data["type"], area_name=data["areaName"].strip(), scheduled_for=data.get("scheduledFor"), personnel=max(0, int(data.get("personnel") or 0)), notes=(data.get("notes") or "").strip(), status=data.get("status") if data.get("status") in ("draft", "scheduled", "active") else "draft", created_by_id=_user_id())
    db.session.add(item); db.session.commit()
    return jsonify({"plan": item.to_dict()}), 201


@command_bp.get("/logs")
@jwt_required()
@require_role("admin")
def list_logs():
    return jsonify({"logs": [x.to_dict() for x in OfficerDailyLog.query.order_by(OfficerDailyLog.created_at.desc()).all()]})


@command_bp.post("/logs")
@jwt_required()
@require_role("officer", "admin")
def create_log():
    data = request.get_json(silent=True) or {}
    if not all(data.get(k) for k in ("date", "shift", "areaName", "summary")):
        return jsonify({"error": "date, shift, areaName and summary are required"}), 400
    item = OfficerDailyLog(officer_id=_user_id(), log_date=data["date"], shift=data["shift"], area_name=data["areaName"].strip(), summary=data["summary"].strip())
    db.session.add(item); db.session.commit()
    return jsonify({"log": item.to_dict()}), 201
