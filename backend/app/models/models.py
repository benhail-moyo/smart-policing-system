from datetime import datetime, timezone

from geoalchemy2 import Geometry
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="community")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship back to incidents they reported
    incidents = db.relationship("Incident", back_populates="reported_by", lazy="dynamic")

    def set_password(self, password: str):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
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
    severity = db.Column(db.String(50))                     # HIGH | MEDIUM | LOW
    triage_confidence = db.Column(db.Float)                 # 0.0 – 1.0
    triage_summary = db.Column(db.Text)                     # English one-sentence summary
    raw_gemini_response = db.Column(db.Text)                # Full Gemini output for audit

    # Workflow status
    status = db.Column(db.String(50), nullable=False, default="PENDING")
    # Allowed: PENDING | TRIAGED | ASSIGNED | RESOLVED

    # Location
    location = db.Column(Geometry("POINT", srid=4326))
    location_description = db.Column(db.Text)

    # Who submitted this report
    reported_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reported_by = db.relationship("User", back_populates="incidents")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        from geoalchemy2.shape import to_shape
        loc = None
        if self.location:
            pt = to_shape(self.location)
            loc = {"lat": pt.y, "lng": pt.x}
        return {
            "id": self.id,
            "raw_text": self.raw_text,
            "language_detected": self.language_detected,
            "category": self.category,
            "severity": self.severity,
            "triage_confidence": self.triage_confidence,
            "triage_summary": self.triage_summary,
            "status": self.status,
            "location": loc,
            "location_description": self.location_description,
            "reported_by_id": self.reported_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Hotspot(db.Model):
    __tablename__ = "hotspot"

    id = db.Column(db.Integer, primary_key=True)
    boundary = db.Column(Geometry("POLYGON", srid=4326))
    centroid = db.Column(Geometry("POINT", srid=4326))
    incident_count = db.Column(db.Integer, nullable=False, default=0)
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    dominant_category = db.Column(db.String(120))
    analysis_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        from geoalchemy2.shape import to_shape
        ctr = None
        if self.centroid:
            pt = to_shape(self.centroid)
            ctr = {"lat": pt.y, "lng": pt.x}
        return {
            "id": self.id,
            "centroid": ctr,
            "incident_count": self.incident_count,
            "risk_score": self.risk_score,
            "dominant_category": self.dominant_category,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
        }


class PatrolRoute(db.Model):
    __tablename__ = "patrol_route"

    id = db.Column(db.Integer, primary_key=True)
    algorithm = db.Column(db.String(50), nullable=False)        # dijkstra | genetic
    route_geometry = db.Column(Geometry("LINESTRING", srid=4326))
    total_distance_km = db.Column(db.Float, nullable=False)
    estimated_fuel_litres = db.Column(db.Float, nullable=False)
    estimated_time_minutes = db.Column(db.Float, nullable=False)
    hotspots_covered = db.Column(db.Integer, nullable=False)
    hotspot_ids = db.Column(db.JSON, nullable=False, default=list)
    computation_time_ms = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
