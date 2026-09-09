from datetime import datetime, timezone
import uuid

from werkzeug.security import generate_password_hash, check_password_hash
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy.dialects.postgresql import UUID

from app import db


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="community")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship back to incidents they reported
    incidents = db.relationship("Incident", back_populates="reported_by", lazy="dynamic", foreign_keys="Incident.reported_by_id")

    def set_password(self, password: str):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name or self.email.split("@")[0],
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Incident(db.Model):
    __tablename__ = "incident"

    id = db.Column(db.Integer, primary_key=True)

    # Raw report text as submitted (may be Shona, Ndebele, or English)
    raw_text = db.Column(db.Text, nullable=False)

    # NLP triage outputs
    language_detected = db.Column(db.String(10))            # 'en' | 'sn' | 'nd'
    category = db.Column(db.String(120))                    # see CLASSIFICATION_PROMPT
    severity = db.Column(db.String(50))                     # HIGH | MEDIUM | LOW or numeric string
    triage_confidence = db.Column(db.Float)                 # 0.0 – 1.0
    triage_summary = db.Column(db.Text)                     # English one-sentence summary
    raw_gemini_response = db.Column(db.Text)                # Full Gemini output for audit

    # Entity extraction results (stored as JSON)
    extracted_entities = db.Column(db.JSON)                # Names, vehicles, locations, weapons, etc.

    # Manual override fields for officers/admins
    manual_severity = db.Column(db.String(50))              # Officer can override severity
    manual_category = db.Column(db.String(120))             # Officer can override category
    override_reason = db.Column(db.Text)                    # Reason for override
    override_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    override_by = db.relationship("User", foreign_keys=[override_by_id])
    override_at = db.Column(db.DateTime, nullable=True)

    # Workflow status
    status = db.Column(db.String(50), nullable=False, default="PENDING")
    # Allowed: PENDING | TRIAGED | ASSIGNED | RESOLVED

    # Location (simplified for SQLite compatibility)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    location_description = db.Column(db.Text)

    # Who submitted this report
    reported_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reported_by = db.relationship("User", back_populates="incidents", foreign_keys=[reported_by_id])

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # When the event happened, distinct from when the report was submitted.
    occurred_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        lat = self.lat or -17.8292
        lng = self.lng or 31.0522
        loc = {"lat": lat, "lng": lng}

        # Use manual override if available, otherwise use NLP triage
        effective_severity = self.manual_severity or self.severity
        effective_category = self.manual_category or self.category

        # Derive priority string for frontend
        sev_str = str(effective_severity or "").upper()
        if sev_str == "HIGH" or sev_str == "5" or sev_str == "4":
            priority = "critical" if sev_str in ("HIGH", "5") else "high"
        elif sev_str == "MEDIUM" or sev_str == "3":
            priority = "medium"
        else:
            priority = "low"

        status_lower = (self.status or "reported").lower()
        if status_lower in ("pending", "triaged"):
            status_lower = "reported"

        reporter_name = self.reported_by.name if self.reported_by and self.reported_by.name else "Anonymous"

        return {
            "id": self.id,
            "raw_text": self.raw_text,
            "description": self.raw_text,
            "language_detected": self.language_detected,
            "category": effective_category or "General",
            "type": effective_category or "General",
            "severity": 5 if priority == "critical" else 4 if priority == "high" else 3 if priority == "medium" else 2,
            "priority": priority,
            "triage_confidence": self.triage_confidence,
            "triageScore": round((self.triage_confidence or 0.8) * 100),
            "triage_summary": self.triage_summary,
            "extracted_entities": self.extracted_entities or {},
            "manual_severity": self.manual_severity,
            "manual_category": self.manual_category,
            "override_reason": self.override_reason,
            "status": status_lower,
            "location": loc,
            "lat": lat,
            "lng": lng,
            "suburb": self.location_description or "Harare",
            "location_description": self.location_description,
            "reported_by_id": self.reported_by_id,
            "reportedBy": reporter_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "occurredAt": self.occurred_at.isoformat() if self.occurred_at else None,
        }


class Hotspot(db.Model):
    __tablename__ = "hotspot"

    hotspot_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    centroid = db.Column(Geometry('POINT', srid=4326), nullable=False)
    convex_hull = db.Column(Geometry('POLYGON', srid=4326))
    dominant_category = db.Column(db.String(120))
    incident_count = db.Column(db.Integer, nullable=False, default=0)
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='emerging')  # 'emerging', 'active', 'cooling', 'dormant'
    consecutive_misses = db.Column(db.Integer, nullable=False, default=0)
    first_detected_at = db.Column(db.DateTime, nullable=False)
    last_matched_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        geom = to_shape(self.centroid)
        
        score = float(self.risk_score or 0.0)
        level = "high" if score >= 0.6 else "medium" if score >= 0.3 else "low"
        weight = round(score * 10, 1)

        return {
            "hotspot_id": str(self.hotspot_id),
            "centroid": {"lat": geom.y, "lng": geom.x},
            "lat": geom.y,
            "lng": geom.x,
            "count": self.incident_count,
            "weight": weight,
            "radius": min(900, 300 + self.incident_count * 70),
            "level": level,
            "topTypes": [self.dominant_category] if self.dominant_category else ["Theft", "Robbery"],
            "incident_count": self.incident_count,
            "risk_score": self.risk_score,
            "dominant_category": self.dominant_category,
            "status": self.status,
            "consecutive_misses": self.consecutive_misses,
            "first_detected_at": self.first_detected_at.isoformat() if self.first_detected_at else None,
            "last_matched_at": self.last_matched_at.isoformat() if self.last_matched_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class HotspotHistory(db.Model):
    __tablename__ = "hotspot_history"

    history_id = db.Column(db.Integer, primary_key=True)
    hotspot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("hotspot.hotspot_id"), nullable=False)
    run_timestamp = db.Column(db.DateTime, nullable=False)
    centroid = db.Column(Geometry('POINT', srid=4326), nullable=False)
    incident_count = db.Column(db.Integer, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    volume_score = db.Column(db.Float, nullable=False)
    severity_score = db.Column(db.Float, nullable=False)
    recency_score = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    dominant_category = db.Column(db.String(120))

    def to_dict(self):
        geom = to_shape(self.centroid)
        
        return {
            "history_id": self.history_id,
            "hotspot_id": str(self.hotspot_id),
            "run_timestamp": self.run_timestamp.isoformat() if self.run_timestamp else None,
            "centroid": {"lat": geom.y, "lng": geom.x},
            "incident_count": self.incident_count,
            "risk_score": self.risk_score,
            "volume_score": self.volume_score,
            "severity_score": self.severity_score,
            "recency_score": self.recency_score,
            "status": self.status,
            "dominant_category": self.dominant_category,
        }


class PatrolRoute(db.Model):
    __tablename__ = "patrol_route"

    id = db.Column(db.Integer, primary_key=True)
    algorithm = db.Column(db.String(50), nullable=False)        # dijkstra | genetic
    # Simplified route storage for SQLite compatibility
    waypoints = db.Column(db.JSON, nullable=False, default=list)
    total_distance_km = db.Column(db.Float, nullable=False)
    estimated_fuel_litres = db.Column(db.Float, nullable=False)
    estimated_time_minutes = db.Column(db.Float, nullable=False)
    hotspots_covered = db.Column(db.Integer, nullable=False)
    hotspot_ids = db.Column(db.JSON, nullable=False, default=list)
    computation_time_ms = db.Column(db.Float, nullable=False)
    # Multi-vehicle support
    vehicle_id = db.Column(db.Integer, nullable=True)           # Vehicle identifier (0-indexed)
    generation_id = db.Column(db.String(36), nullable=True)     # UUID grouping routes from same request
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        waypoints = self.waypoints if self.waypoints else [
            {"lat": -17.8292, "lng": 31.0522},
            {"lat": -17.8252, "lng": 31.0475},
            {"lat": -17.8189, "lng": 31.0433},
            {"lat": -17.8292, "lng": 31.0522},
        ]

        algo_name = self.algorithm.title() if self.algorithm else "Dijkstra"
        color = "#2563eb" if self.algorithm == "dijkstra" else "#f97316"

        # Multi-vehicle display name
        if self.vehicle_id is not None:
            name = f"Vehicle {self.vehicle_id + 1} — {algo_name} Optimized"
        else:
            name = f"Route {self.id} — {algo_name} Optimized"

        return {
            "id": f"route-{self.id}",
            "name": name,
            "color": color,
            "algorithm": self.algorithm,
            "waypoints": waypoints,
            "distanceKm": self.total_distance_km,
            "total_distance_km": self.total_distance_km,
            "estimated_fuel_litres": self.estimated_fuel_litres,
            "estimated_time_minutes": self.estimated_time_minutes,
            "hotspots_covered": self.hotspots_covered,
            "hotspot_ids": self.hotspot_ids,
            "computation_time_ms": self.computation_time_ms,
            "vehicle_id": self.vehicle_id,
            "generation_id": self.generation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    """
    Immutable audit log for tracking automated recommendations and human overrides.
    Supports multi-vehicle route override tracking with vehicle identification.
    """
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)     # 'incident', 'route', 'hotspot', etc.
    entity_id = db.Column(db.String(100), nullable=False)      # ID of the affected entity
    action = db.Column(db.String(50), nullable=False)          # 'created', 'updated', 'overridden', 'deleted'
    
    # Original values before change
    previous_state = db.Column(db.JSON, nullable=True)
    
    # New values after change
    new_state = db.Column(db.JSON, nullable=True)
    
    # Override-specific fields
    override_reason = db.Column(db.Text, nullable=True)
    override_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    override_by = db.relationship("User", foreign_keys=[override_by_id])
    
    # Multi-vehicle support for route overrides
    vehicle_id = db.Column(db.Integer, nullable=True)          # Vehicle identifier for route overrides
    generation_id = db.Column(db.String(36), nullable=True)    # Generation ID for route overrides
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)       # For security audit
    
    def to_dict(self):
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "override_reason": self.override_reason,
            "override_by": self.override_by.name if self.override_by else None,
            "override_by_id": self.override_by_id,
            "vehicle_id": self.vehicle_id,
            "generation_id": self.generation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ip_address": self.ip_address,
        }


class Deployment(db.Model):
    """A command-centre dispatch marker for either foot or vehicle personnel."""
    __tablename__ = "deployment"

    id = db.Column(db.Integer, primary_key=True)
    unit_type = db.Column(db.String(20), nullable=False)  # foot | vehicle
    area_name = db.Column(db.String(160), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="active")
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {"id": self.id, "unitType": self.unit_type, "areaName": self.area_name,
                "lat": self.lat, "lng": self.lng, "instructions": self.instructions or "",
                "status": self.status, "createdAt": self.created_at.isoformat() if self.created_at else None}


class StrategicPlan(db.Model):
    __tablename__ = "strategic_plan"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    plan_type = db.Column(db.String(60), nullable=False)
    area_name = db.Column(db.String(160), nullable=False)
    scheduled_for = db.Column(db.String(80), nullable=True)
    personnel = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="draft")
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {"id": self.id, "title": self.title, "type": self.plan_type, "areaName": self.area_name,
                "scheduledFor": self.scheduled_for, "personnel": self.personnel, "notes": self.notes or "",
                "status": self.status, "createdAt": self.created_at.isoformat() if self.created_at else None}


class OfficerDailyLog(db.Model):
    __tablename__ = "officer_daily_log"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    log_date = db.Column(db.String(10), nullable=False)
    shift = db.Column(db.String(50), nullable=False)
    area_name = db.Column(db.String(160), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="submitted")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    officer = db.relationship("User", foreign_keys=[officer_id])

    def to_dict(self):
        return {"id": self.id, "officer": self.officer.name if self.officer else "Officer",
                "date": self.log_date, "shift": self.shift, "areaName": self.area_name,
                "summary": self.summary, "status": self.status,
                "createdAt": self.created_at.isoformat() if self.created_at else None}
