"""
Incidents API — Crime-Watch
============================
Endpoints:
  POST /api/v1/incidents/        Submit + triage a crime report
  GET  /api/v1/incidents/        List incidents (filterable by severity)
  GET  /api/v1/incidents/<id>    Get single incident
  GET  /api/v1/incidents/stats   Count by severity (dashboard use)
  PUT  /api/v1/incidents/<id>/override  Override triage (officers/admin)
  GET  /api/v1/incidents/search   Advanced search (officers/admin)
"""
import re
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app import db
from app.models.models import Incident, User
from app.services.nlp.triage import triage_service
from app.security.decorators import login_required, role_required

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


def _parse_occurred_at(value):
    """Parse an optional ISO-8601 occurrence time supplied by the report form."""
    if not value:
        return None
    if not isinstance(value, str):
        raise ValueError("occurredAt must be an ISO-8601 date and time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("occurredAt must be a valid date and time") from exc
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


# ── POST /api/v1/incidents/ ────────────────────────────────────────────────

@incidents_bp.post("/")
@jwt_required(optional=True)
def create_incident():
    """
    Submit and triage a crime report.

    Supports both frontend format:
      { type, description, severity, suburb, lat, lng }
    and backend format:
      { raw_text, location_lat, location_lng, location_description }
    """
    data = request.get_json(silent=True) or {}

    raw_text = (data.get("raw_text") or data.get("description") or "").strip()

    if not raw_text:
        return jsonify({"error": "Description or raw_text is required"}), 400

    if len(raw_text) < 3:
        return jsonify({"error": "Report too short to classify"}), 400

    if len(raw_text) > 5000:
        return jsonify({"error": "Report exceeds maximum length of 5000 characters"}), 400

    # ── Run NLP triage ────────────────────────────────────────────────────
    try:
        triage_result = triage_service.triage(raw_text)
    except Exception as exc:
        # Return a JSON error so frontend receives structured response
        return jsonify({"error": f"Triage failed: {exc}"}), 500

    # Category from frontend or NLP triage
    category = data.get("type") or triage_result.get("category") or "General"
    # Severity always determined by NLP triage engine
    severity = triage_result.get("severity", "MEDIUM")

    # ── Resolve submitting user ────────────────────────────────────────────
    raw_user_id = get_jwt_identity()
    user_id = int(raw_user_id) if raw_user_id and str(raw_user_id).isdigit() else None

    lat = data.get("lat") if data.get("lat") is not None else data.get("location_lat")
    lng = data.get("lng") if data.get("lng") is not None else data.get("location_lng")
    suburb = data.get("suburb") or data.get("location_description") or "Harare"
    try:
        occurred_at = _parse_occurred_at(data.get("occurredAt") or data.get("occurred_at"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # ── Build and persist Incident ─────────────────────────────────────────
    # Persist incident using simplified lat/lng fields (SQLite-compatible schema)
    incident = Incident(
        raw_text=raw_text,
        language_detected=triage_result.get("language_detected", "en"),
        category=category,
        severity=severity,
        triage_confidence=triage_result.get("confidence", 0.85),
        triage_summary=triage_result.get("summary", raw_text[:100]),
        raw_gemini_response=triage_result.get("raw_gemini_response"),
        extracted_entities=triage_result.get("entities", {}),
        status="TRIAGED",
        lat=float(lat) if lat is not None else None,
        lng=float(lng) if lng is not None else None,
        location_description=suburb,
        reported_by_id=user_id,
        occurred_at=occurred_at,
    )

    db.session.add(incident)
    db.session.commit()

    inc_dict = incident.to_dict()
    triage_payload = {
        "priority": inc_dict["priority"],
        "score": inc_dict["triageScore"],
        "recommendation": triage_result.get("reasoning") or triage_result.get("summary") or "Dispatch patrol unit as priority.",
        "eta": "0-5 min" if inc_dict["priority"] == "critical" else "5-15 min" if inc_dict["priority"] == "high" else "15-45 min" if inc_dict["priority"] == "medium" else "1-4 hrs",
        "language_detected": triage_result.get("language_detected"),
        "category": category,
        "severity": severity,
        "confidence": triage_result.get("confidence"),
        "summary": triage_result.get("summary"),
    }

    return jsonify({
        "message": "Incident submitted and triaged successfully.",
        "incident": inc_dict,
        "triage": triage_payload,
    }), 201


# ── GET /api/v1/incidents/ ─────────────────────────────────────────────────

@incidents_bp.get("/")
@jwt_required(optional=True)
def list_incidents():
    """
    List incidents. Officers/admins see all; community users see only their own.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id and str(user_id).isdigit() else None

    severity_filter = request.args.get("severity", "").upper()
    try:
        limit = min(int(request.args.get("limit", 500)), 1000)
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        limit, offset = 500, 0

    query = db.session.query(Incident)

    if user and user.role == "community":
        query = query.filter(Incident.reported_by_id == user.id)

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
@jwt_required(optional=True)
def get_stats():
    """
    Returns full incident statistics and 7-day trends for the React dashboard.
    """
    incidents = db.session.query(Incident).all()
    total = len(incidents)

    by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_status = {"reported": 0, "dispatched": 0, "resolved": 0}
    by_type = {}

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    day_sec = 86400
    last_24h = 0
    last_7d = 0

    for inc in incidents:
        d = inc.to_dict()
        p = d.get("priority", "medium")
        by_priority[p] = by_priority.get(p, 0) + 1

        st = d.get("status", "reported")
        if st not in by_status:
            st = "reported"
        by_status[st] = by_status.get(st, 0) + 1

        t = d.get("type", "General")
        by_type[t] = by_type.get(t, 0) + 1

        if inc.created_at:
            created = inc.created_at.replace(tzinfo=timezone.utc) if inc.created_at.tzinfo is None else inc.created_at
            age_sec = (now - created).total_seconds()
            if age_sec <= day_sec:
                last_24h += 1
            if age_sec <= 7 * day_sec:
                last_7d += 1

    top_types = [
        {"type": t, "count": c}
        for t, c in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:6]
    ]

    # 7-day trend
    trend = []
    for i in range(6, -1, -1):
        target_day = now - timedelta(days=i)
        day_str = target_day.strftime("%a")
        day_start = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = target_day.replace(hour=23, minute=59, second=59, microsecond=999999)

        count = 0
        for inc in incidents:
            if inc.created_at:
                created = inc.created_at.replace(tzinfo=timezone.utc) if inc.created_at.tzinfo is None else inc.created_at
                if day_start <= created <= day_end:
                    count += 1
        trend.append({"day": day_str, "count": count})

    open_cases = by_status.get("reported", 0) + by_status.get("dispatched", 0)
    resolution_rate = round((by_status.get("resolved", 0) / total * 100)) if total > 0 else 0

    return jsonify({
        "total": total,
        "openCases": open_cases,
        "resolutionRate": resolution_rate,
        "last24h": last_24h,
        "last7d": last_7d,
        "byPriority": by_priority,
        "byStatus": by_status,
        "topTypes": top_types,
        "trend": trend,
    }), 200


# ── GET /api/v1/incidents/<id> ─────────────────────────────────────────────

@incidents_bp.get("/<int:incident_id>")
@jwt_required(optional=True)
def get_incident(incident_id: int):
    """
    Retrieve a single incident by ID with full details.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id and str(user_id).isdigit() else None
    
    incident = db.session.get(Incident, incident_id)
    if not incident:
        return jsonify({"error": "Incident not found"}), 404

    # Community users can only see their own incidents
    if user and user.role == "community" and incident.reported_by_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"incident": incident.to_dict()}), 200


# ── PUT /api/v1/incidents/<id>/override ───────────────────────────────────────

@incidents_bp.put("/<int:incident_id>/override")
@jwt_required()
@require_role("officer", "admin")
def override_incident(incident_id: int):
    """
    Override triage assessment (officers/admin only).
    Allows manual modification of severity, category, and provides reason.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    incident = db.session.get(Incident, incident_id)
    if not incident:
        return jsonify({"error": "Incident not found"}), 404

    data = request.get_json(silent=True) or {}
    
    # Validate override fields
    valid_severities = ["HIGH", "MEDIUM", "LOW"]
    manual_severity = data.get("manual_severity")
    if manual_severity and manual_severity not in valid_severities:
        return jsonify({"error": f"Invalid severity. Must be one of: {valid_severities}"}), 400

    valid_categories = ["murder", "assault", "robbery", "rape", "theft", "burglary", 
                       "vandalism", "drug_offence", "fraud", "suspicious_activity", 
                       "noise_complaint", "domestic_dispute", "other"]
    manual_category = data.get("manual_category")
    if manual_category and manual_category not in valid_categories:
        return jsonify({"error": f"Invalid category. Must be one of: {valid_categories}"}), 400

    override_reason = data.get("override_reason")
    if not override_reason:
        return jsonify({"error": "Override reason is required"}), 400

    # Apply override
    incident.manual_severity = manual_severity
    incident.manual_category = manual_category
    incident.override_reason = override_reason
    incident.override_by_id = user.id
    incident.override_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify({
        "message": "Incident triage override applied successfully",
        "incident": incident.to_dict()
    }), 200


# ── GET /api/v1/incidents/search ────────────────────────────────────────────

@incidents_bp.get("/search")
@jwt_required()
@require_role("officer", "admin")
def search_incidents():
    """
    Advanced search and filtering for incidents (officers/admin only).
    Supports filtering by date, time, location, risk score, category, and incident ref.
    """
    try:
        # Get filter parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        category = request.args.get("category")
        severity = request.args.get("severity", "").upper()
        status = request.args.get("status", "").upper()
        location = request.args.get("location")
        min_confidence = request.args.get("min_confidence")
        search_query = request.args.get("q")  # Full-text search
        
        # Pagination
        try:
            limit = min(int(request.args.get("limit", 50)), 200)
            offset = int(request.args.get("offset", 0))
        except (TypeError, ValueError):
            limit, offset = 50, 0

        query = db.session.query(Incident)

        # Apply filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
                query = query.filter(Incident.created_at >= start_dt)
            except ValueError:
                return jsonify({"error": "Invalid start_date format"}), 400

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
                query = query.filter(Incident.created_at <= end_dt)
            except ValueError:
                return jsonify({"error": "Invalid end_date format"}), 400

        if category:
            query = query.filter(Incident.category == category)

        if severity in ("HIGH", "MEDIUM", "LOW"):
            query = query.filter(Incident.severity == severity)

        if status:
            query = query.filter(Incident.status == status)

        if location:
            query = query.filter(Incident.location_description.ilike(f"%{location}%"))

        if min_confidence:
            try:
                min_conf = float(min_confidence)
                query = query.filter(Incident.triage_confidence >= min_conf)
            except ValueError:
                return jsonify({"error": "Invalid min_confidence value"}), 400

        if search_query:
            query = query.filter(Incident.raw_text.ilike(f"%{search_query}%"))

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
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
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "category": category,
                "severity": severity,
                "status": status,
                "location": location,
                "min_confidence": min_confidence,
                "search_query": search_query
            }
        }), 200

    except Exception as exc:
        return jsonify({"error": f"Search failed: {exc}"}), 500

