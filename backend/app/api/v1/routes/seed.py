from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.models import User, Incident, Hotspot, PatrolRoute

seed_bp = Blueprint("seed", __name__)


HARARE_SAMPLE_INCIDENTS = [
    {
        "type": "Armed Robbery",
        "description": "Two armed individuals intercepted a delivery vehicle near Sam Nujoma St and Jason Moyo Ave, demanding cash.",
        "suburb": "CBD",
        "severity": "HIGH",
        "lat": -17.8292,
        "lng": 31.0522,
    },
    {
        "type": "Burglary",
        "description": "Break-in reported at a retail store along Robert Mugabe Rd overnight. High value goods taken.",
        "suburb": "CBD",
        "severity": "HIGH",
        "lat": -17.8310,
        "lng": 31.0540,
    },
    {
        "type": "Carjacking",
        "description": "Vehicle stolen at gunpoint near Mbare Musika bus station during evening hours.",
        "suburb": "Mbare",
        "severity": "HIGH",
        "lat": -17.8564,
        "lng": 31.0301,
    },
    {
        "type": "Theft",
        "description": "Pickpocketing incident reported at crowded market area in Mbare.",
        "suburb": "Mbare",
        "severity": "MEDIUM",
        "lat": -17.8540,
        "lng": 31.0330,
    },
    {
        "type": "Assault",
        "description": "Physical alteration outside a public venue in Avondale shopping center.",
        "suburb": "Avondale",
        "severity": "MEDIUM",
        "lat": -17.7950,
        "lng": 31.0380,
    },
    {
        "type": "Fraud",
        "description": "Financial scam reported at bank branch near Samora Machel Ave.",
        "suburb": "CBD",
        "severity": "MEDIUM",
        "lat": -17.8240,
        "lng": 31.0490,
    },
    {
        "type": "Vandalism",
        "description": "Property damage to public street lighting infrastructure in Eastlea.",
        "suburb": "Eastlea",
        "severity": "LOW",
        "lat": -17.8220,
        "lng": 31.0750,
    },
]


def _build_location(lat, lng):
    return float(lat), float(lng)


@seed_bp.post("/")
@jwt_required(optional=True)
def seed_database():
    # 1. Ensure default users exist
    admin_user = db.session.query(User).filter_by(email="admin@harare.gov.zw").first()
    if not admin_user:
        admin_user = User(
            name="Command Admin",
            email="admin@harare.gov.zw",
            role="admin",
        )
        admin_user.set_password("password123")
        db.session.add(admin_user)

    officer_user = db.session.query(User).filter_by(email="officer@harare.gov.zw").first()
    if not officer_user:
        officer_user = User(
            name="Officer Chikwava",
            email="officer@harare.gov.zw",
            role="officer",
        )
        officer_user.set_password("password123")
        db.session.add(officer_user)

    community_user = db.session.query(User).filter_by(email="community@harare.gov.zw").first()
    if not community_user:
        community_user = User(
            name="Tendai Moyo",
            email="community@harare.gov.zw",
            role="community",
        )
        community_user.set_password("password123")
        db.session.add(community_user)

    db.session.commit()

    # 2. Add sample incidents if count is low
    count = db.session.query(Incident).count()
    added_incidents = 0
    if count < 5:
        now = datetime.now(timezone.utc)
        for i, item in enumerate(HARARE_SAMPLE_INCIDENTS):
            inc = Incident(
                raw_text=item["description"],
                language_detected="en",
                category=item["type"],
                severity=item["severity"],
                triage_confidence=0.92,
                triage_summary=item["description"][:100],
                status="RESOLVED" if i % 3 == 0 else "TRIAGED",
                location=_build_point(item["lat"], item["lng"]),
                location_description=item["suburb"],
                reported_by_id=officer_user.id if officer_user else None,
                created_at=now - timedelta(days=i * 2, hours=i * 3),
            )
            db.session.add(inc)
            added_incidents += 1
        db.session.commit()

    # 3. Add sample hotspots if empty
    hotspot_count = db.session.query(Hotspot).count()
    if hotspot_count == 0:
        from geoalchemy2.shape import from_shape
        from shapely.geometry import Point, Polygon
        h1 = Hotspot(
            centroid=from_shape(Point(31.0522, -17.8292), srid=4326),
            boundary=from_shape(Polygon([(31.045, -17.825), (31.060, -17.825), (31.060, -17.835), (31.045, -17.835)]), srid=4326),
            incident_count=14,
            risk_score=0.85,
            dominant_category="Armed Robbery",
            analysis_date=datetime.now(timezone.utc),
        )
        h2 = Hotspot(
            centroid=from_shape(Point(31.0301, -17.8564), srid=4326),
            boundary=from_shape(Polygon([(31.025, -17.850), (31.038, -17.850), (31.038, -17.865), (31.025, -17.865)]), srid=4326),
            incident_count=9,
            risk_score=0.68,
            dominant_category="Carjacking",
            analysis_date=datetime.now(timezone.utc),
        )
        db.session.add_all([h1, h2])
        db.session.commit()

    total_users = db.session.query(User).count()
    total_incidents = db.session.query(Incident).count()

    return jsonify({
        "seeded": True,
        "users": total_users,
        "incidents": total_incidents,
        "demoAccounts": [
            { "role": "officer", "email": "officer@harare.gov.zw", "password": "password123" },
            { "role": "admin", "email": "admin@harare.gov.zw", "password": "password123" },
            { "role": "community", "email": "community@harare.gov.zw", "password": "password123" },
        ],
    }), 200
