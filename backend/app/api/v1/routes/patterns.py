"""
Pattern Detection API Routes
============================
Endpoints for incident pattern analysis and detection.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app import db
from app.models.models import Incident, User
from app.services.pattern_detection.pattern_recognizer import PatternRecognizer
from app.services.pattern_detection.similarity_engine import SimilarityEngine

patterns_bp = Blueprint("patterns", __name__)


@patterns_bp.post("/analyze-incident")
@jwt_required()
def analyze_incident_patterns():
    """
    Analyze a specific incident for related patterns.
    
    Request: { "incident_id": int }
    Response: { "related_incidents": [...], "potential_patterns": [...] }
    """
    data = request.get_json()
    incident_id = data.get("incident_id")
    
    if not incident_id:
        return jsonify({"error": "incident_id required"}), 400
    
    incident = Incident.query.get(incident_id)
    if not incident:
        return jsonify({"error": "Incident not found"}), 404
    
    # Find related incidents
    similarity_engine = SimilarityEngine()
    related_incidents = similarity_engine.find_related_incidents(
        incident, 
        hours_back=48, 
        min_similarity=0.7
    )
    
    # Check for patterns involving this incident
    pattern_recognizer = PatternRecognizer()
    time_cutoff = datetime.utcnow() - timedelta(days=30)
    recent_incidents = Incident.query.filter(
        Incident.created_at >= time_cutoff
    ).all()
    
    all_patterns = pattern_recognizer.detect_all_patterns(days_back=30)
    
    # Filter patterns that include this incident
    relevant_patterns = [
        pattern for pattern in all_patterns['serial_crimes'] + 
        all_patterns['crime_sprees'] + 
        all_patterns['repeat_locations']
        if incident_id in pattern.get('incident_ids', [])
    ]
    
    return jsonify({
        "incident_id": incident_id,
        "related_incidents": related_incidents,
        "potential_patterns": relevant_patterns,
        "analysis_timestamp": datetime.utcnow().isoformat()
    }), 200


@patterns_bp.get("/active")
@jwt_required()
def get_active_patterns():
    """
    Get all currently active crime patterns.
    
    Query params: days_back (default 30)
    Response: { "serial_crimes": [...], "crime_sprees": [...], "repeat_locations": [...] }
    """
    days_back = request.args.get('days_back', 30, type=int)
    
    pattern_recognizer = PatternRecognizer()
    patterns = pattern_recognizer.detect_all_patterns(days_back=days_back)
    
    return jsonify({
        "analysis_period_days": days_back,
        "patterns": patterns,
        "total_patterns": sum(len(v) for v in patterns.values()),
        "analysis_timestamp": datetime.utcnow().isoformat()
    }), 200


@patterns_bp.post("/investigation-start")
@jwt_required()
def start_investigation():
    """
    Mark a pattern as under investigation and create investigation record.
    
    Request: { "pattern_type": str, "incident_ids": [int], "notes": str }
    Response: { "investigation_id": int, "status": "active" }
    """
    data = request.get_json()
    pattern_type = data.get("pattern_type")
    incident_ids = data.get("incident_ids", [])
    notes = data.get("notes", "")
    
    if not pattern_type or not incident_ids:
        return jsonify({"error": "pattern_type and incident_ids required"}), 400
    
    # Create investigation record (would need Investigation model)
    # For now, return success response
    investigation_id = hash(f"{pattern_type}_{','.join(map(str, incident_ids))}_{datetime.utcnow()}")
    
    return jsonify({
        "investigation_id": str(investigation_id),
        "pattern_type": pattern_type,
        "incident_ids": incident_ids,
        "status": "active",
        "created_by": get_jwt_identity(),
        "notes": notes,
        "created_at": datetime.utcnow().isoformat()
    }), 201


@patterns_bp.get("/<pattern_id>/timeline")
@jwt_required()
def get_pattern_timeline(pattern_id):
    """
    Get chronological timeline of incidents in a pattern.
    
    Response: { "incidents": [...], "timeline_events": [...] }
    """
    # This would require pattern persistence in database
    # For now, return a placeholder response
    return jsonify({
        "pattern_id": pattern_id,
        "message": "Pattern timeline feature requires pattern persistence",
        "incidents": [],
        "timeline_events": []
    }), 200
