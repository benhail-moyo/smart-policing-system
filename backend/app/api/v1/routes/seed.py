from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.models import User, Incident, Hotspot, PatrolRoute
from app.services.gis.hotspot_analysis import hotspot_service

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
        "type": "Theft",
        "description": "Bag theft reported near Copacabana rank in the central business district.",
        "suburb": "CBD",
        "severity": "MEDIUM",
        "lat": -17.8278,
        "lng": 31.0503,
    },
    {
        "type": "Assault",
        "description": "Assault reported near the Mbare market transport interchange.",
        "suburb": "Mbare",
        "severity": "HIGH",
        "lat": -17.8553,
        "lng": 31.0316,
    },
    {
        "type": "Theft",
        "description": "Mobile phone theft reported near Mbare Musika market stalls.",
        "suburb": "Mbare",
        "severity": "MEDIUM",
        "lat": -17.8575,
        "lng": 31.0290,
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
@seed_bp.post("")
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

    # 2. Add any missing sample incidents. The dense CBD and Mbare points
    # deliberately satisfy DBSCAN's four-incident minimum for map hotspots.
    added_incidents = 0
    now = datetime.now(timezone.utc)
    for i, item in enumerate(HARARE_SAMPLE_INCIDENTS):
        exists = db.session.query(Incident.id).filter(
            Incident.raw_text == item["description"]
        ).first()
        if exists:
            continue
        inc = Incident(
            raw_text=item["description"],
            language_detected="en",
            category=item["type"],
            severity=item["severity"],
            triage_confidence=0.92,
            triage_summary=item["description"][:100],
            status="RESOLVED" if i % 3 == 0 else "TRIAGED",
            lat=float(item["lat"]),
            lng=float(item["lng"]),
            location_description=item["suburb"],
            reported_by_id=officer_user.id if officer_user else None,
            created_at=now - timedelta(days=i * 2, hours=i * 3),
        )
        db.session.add(inc)
        added_incidents += 1
    db.session.commit()

    # 3. Persist genuine DBSCAN results so the map is useful immediately.
    analysis = hotspot_service.run_hotspot_analysis(days_back=30)

    total_users = db.session.query(User).count()
    total_incidents = db.session.query(Incident).count()

    return jsonify({
        "message": "Seed data installed",
        "seeded": True,
        "users": total_users,
        "incidents": total_incidents,
        "hotspots": analysis["hotspots_generated"],
        "demoAccounts": [
            { "role": "officer", "email": "officer@harare.gov.zw", "password": "password123" },
            { "role": "admin", "email": "admin@harare.gov.zw", "password": "password123" },
            { "role": "community", "email": "community@harare.gov.zw", "password": "password123" },
        ],
    }), 200
