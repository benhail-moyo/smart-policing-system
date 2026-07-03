"""
Incidents API — Crime-Watch
============================
Endpoints:
  POST /api/v1/incidents/        Submit + triage a crime report
  GET  /api/v1/incidents/        List incidents (filterable by severity)
  GET  /api/v1/incidents/<id>    Get single incident
  GET  /api/v1/incidents/stats   Count by severity (dashboard use)
"""
import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app import db
from app.models.models import Incident, User
from app.services.nlp.triage import triage_service

incidents_bp = Blueprint("incidents", __name__)

# ── Helpers ────────────────────────────────────────────────────────────────

def _build_location(lat, lng):
    """Convert float lat/lng to a PostGIS POINT WKT string for GeoAlchemy2."""
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point
    if lat is None or lng is None:
        return None
    try:
        return from_shape(Point(float(lng), float(lat)), srid=4326)
    except (TypeError, ValueError):
        return None


# ── POST /api/v1/incidents/ ────────────────────────────────────────────────

@incidents_bp.post("/")
@jwt_required()
def create_incident():
    """
    Submit and triage a crime report.

    Request body:
      raw_text            str   Required. 5–5000 characters.
      location_lat        float Optional.
      location_lng        float Optional.
      location_description str  Optional.

    Returns 201 with full triage result on success.
    """
    data = request.get_json(silent=True) or {}

    # ── Input validation ───────────────────────────────────────────────────
    raw_text = data.get("raw_text", "").strip()

    if not raw_text:
        return jsonify({"error": "raw_text is required"}), 400

    if len(raw_text) < 5:
        return jsonify({"error": "Report too short to classify"}), 400

    if len(raw_text) > 5000:
        return jsonify({"error": "Report exceeds maximum length of 5000 characters"}), 400

    # ── Run NLP triage ────────────────────────────────────────────────────
    triage_result = triage_service.triage(raw_text)

    # ── Resolve submitting user ────────────────────────────────────────────
    user_id = get_jwt_identity()

    # ── Build and persist Incident ─────────────────────────────────────────
    incident = Incident(
        raw_text=raw_text,
        language_detected=triage_result.get("language_detected", "en"),
        category=triage_result.get("category"),
        severity=triage_result.get("severity"),
        triage_confidence=triage_result.get("confidence"),
        triage_summary=triage_result.get("summary"),
        raw_gemini_response=triage_result.get("raw_gemini_response"),
        status="TRIAGED",
        location=_build_location(
            data.get("location_lat"),
            data.get("location_lng"),
        ),
        location_description=data.get("location_description", ""),
        reported_by_id=user_id,
    )

    db.session.add(incident)
    db.session.commit()

    return jsonify({
        "message": "Incident submitted and triaged successfully.",
        "incident": incident.to_dict(),
        "triage": {
            "language_detected": triage_result.get("language_detected"),
            "category": triage_result.get("category"),
            "severity": triage_result.get("severity"),
            "confidence": triage_result.get("confidence"),
            "summary": triage_result.get("summary"),
            "reasoning": triage_result.get("reasoning"),
        },
    }), 201


# ── GET /api/v1/incidents/ ─────────────────────────────────────────────────

@incidents_bp.get("/")
@jwt_required()
def list_incidents():
    """
    List incidents. Officers/admins see all; community users see only their own.

    Query params:
      severity   Filter by HIGH | MEDIUM | LOW
      limit      Max results (default 50, max 200)
      offset     Pagination offset (default 0)
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    severity_filter = request.args.get("severity", "").upper()
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        limit, offset = 50, 0

    query = db.session.query(Incident)

    # Community reporters only see their own incidents
    if user and user.role == "community":
        query = query.filter(Incident.reported_by_id == user_id)

    if severity_filter in ("HIGH", "MEDIUM", "LOW"):
        query = query.filter(Incident.severity == severity_filter)

    total = query.count()
    incidents = (
        query.order_by(Incident.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return jsonify({
        "incidents": [i.to_dict() for i in incidents],
        "total": total,
        "limit": limit,
        "offset": offset,
    }), 200


# ── GET /api/v1/incidents/stats ────────────────────────────────────────────

@incidents_bp.get("/stats")
@jwt_required()
def get_stats():
    """
    Returns incident counts grouped by severity.
    Used by the React dashboard summary cards.
    """
    results = (
        db.session.query(Incident.severity, func.count(Incident.id))
        .group_by(Incident.severity)
        .all()
    )
    by_severity = {str(sev): count for sev, count in results}
    total = sum(count for _, count in results)

    return jsonify({
        "by_severity": by_severity,
        "total": total,
    }), 200


# ── GET /api/v1/incidents/<id> ─────────────────────────────────────────────

@incidents_bp.get("/<int:incident_id>")
@jwt_required()
def get_incident(incident_id: int):
    """
    Retrieve a single incident by ID.
    Community users may only view their own incidents.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    incident = db.session.get(Incident, incident_id)
    if not incident:
        return jsonify({"error": "Incident not found"}), 404

    # Community reporters can only see their own reports
    if user and user.role == "community" and incident.reported_by_id != user_id:
        return jsonify({"error": "Insufficient permissions"}), 403

    return jsonify({"incident": incident.to_dict()}), 200
