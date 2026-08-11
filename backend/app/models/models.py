from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

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

    # Workflow status
    status = db.Column(db.String(50), nullable=False, default="PENDING")
    # Allowed: PENDING | TRIAGED | ASSIGNED | RESOLVED

    # Location (simplified for SQLite compatibility)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    location_description = db.Column(db.Text)

    # Who submitted this report
    reported_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reported_by = db.relationship("User", back_populates="incidents")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # When the event happened, distinct from when the report was submitted.
    occurred_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        lat = self.lat or -17.8292
        lng = self.lng or 31.0522
        loc = {"lat": lat, "lng": lng}

        # Derive priority string for frontend
        sev_str = str(self.severity or "").upper()
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
            "category": self.category or "General",
            "type": self.category or "General",
            "severity": 5 if priority == "critical" else 4 if priority == "high" else 3 if priority == "medium" else 2,
            "priority": priority,
            "triage_confidence": self.triage_confidence,
            "triageScore": round((self.triage_confidence or 0.8) * 100),
            "triage_summary": self.triage_summary,
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

    id = db.Column(db.Integer, primary_key=True)
    # Simplified location for SQLite compatibility
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    incident_count = db.Column(db.Integer, nullable=False, default=0)
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    dominant_category = db.Column(db.String(120))
    analysis_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        lat = self.lat or -17.8292
        lng = self.lng or 31.0522
        ctr = {"lat": lat, "lng": lng}

        score = float(self.risk_score or 0.0)
        level = "high" if score >= 0.6 else "medium" if score >= 0.3 else "low"
        weight = round(score * 10, 1)

        return {
            "id": self.id,
            "centroid": ctr,
            "lat": lat,
            "lng": lng,
            "count": self.incident_count,
            "weight": weight,
            "radius": min(900, 300 + self.incident_count * 70),
            "level": level,
            "topTypes": [self.dominant_category] if self.dominant_category else ["Theft", "Robbery"],
            "incident_count": self.incident_count,
            "risk_score": self.risk_score,
            "dominant_category": self.dominant_category,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
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

        return {
            "id": f"route-{self.id}",
            "name": f"Route {self.id} — {algo_name} Optimized",
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
