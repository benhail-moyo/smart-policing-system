from datetime import datetime, timezone

from geoalchemy2 import Geometry

from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="analyst")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(120))
    severity = db.Column(db.String(50))
    language = db.Column(db.String(50))
    location = db.Column(Geometry("POINT", srid=4326))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Hotspot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(120))
    centroid = db.Column(Geometry("POINT", srid=4326))
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    incident_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class PatrolRoute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    algorithm = db.Column(db.String(50), nullable=False)
    route_geometry = db.Column(Geometry("LINESTRING", srid=4326))
    total_distance_km = db.Column(db.Float, nullable=False)
    estimated_fuel_litres = db.Column(db.Float, nullable=False)
    estimated_time_minutes = db.Column(db.Float, nullable=False)
    hotspots_covered = db.Column(db.Integer, nullable=False)
    hotspot_ids = db.Column(db.JSON, nullable=False, default=list)
    computation_time_ms = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
