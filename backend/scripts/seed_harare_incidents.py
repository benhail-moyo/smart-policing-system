#!/usr/bin/env python3
"""
Seed clustered synthetic Harare incidents for GIS hotspot analysis.

Run from the repository root:
    python backend/scripts/seed_harare_incidents.py
"""
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app import create_app, db
from app.models.models import Incident, User


HARARE_HOTSPOT_ZONES = [
    {
        "name": "Mbare",
        "center": (-17.8677, 31.0359),
        "radius_deg": 0.015,
        "incident_types": ["robbery", "assault", "theft"],
        "n_incidents": 22,
        "severity_weights": ["HIGH", "HIGH", "MEDIUM", "MEDIUM", "LOW"],
    },
    {
        "name": "Highfields",
        "center": (-17.8900, 31.0100),
        "radius_deg": 0.012,
        "incident_types": ["drug_offence", "theft", "vandalism"],
        "n_incidents": 18,
        "severity_weights": ["HIGH", "MEDIUM", "MEDIUM", "LOW"],
    },
    {
        "name": "Harare CBD",
        "center": (-17.8292, 31.0522),
        "radius_deg": 0.010,
        "incident_types": ["robbery", "fraud", "suspicious_activity"],
        "n_incidents": 25,
        "severity_weights": ["HIGH", "HIGH", "HIGH", "MEDIUM", "LOW"],
    },
    {
        "name": "Budiriro",
        "center": (-17.9100, 31.0200),
        "radius_deg": 0.013,
        "incident_types": ["domestic_dispute", "assault", "theft"],
        "n_incidents": 15,
        "severity_weights": ["MEDIUM", "MEDIUM", "LOW", "LOW"],
    },
    {
        "name": "Chitungwiza",
        "center": (-18.0130, 31.0750),
        "radius_deg": 0.018,
        "incident_types": ["robbery", "theft", "drug_offence"],
        "n_incidents": 20,
        "severity_weights": ["HIGH", "MEDIUM", "MEDIUM", "LOW"],
    },
]


def random_point(center, radius_deg):
    lat_center, lng_center = center
    stddev = radius_deg / 3.0
    lat = lat_center + random.gauss(0, stddev)
    lng = lng_center + random.gauss(0, stddev)
    lat = max(lat_center - radius_deg, min(lat_center + radius_deg, lat))
    lng = max(lng_center - radius_deg, min(lng_center + radius_deg, lng))
    return lat, lng


def ensure_user(email, role, password):
    user = db.session.query(User).filter_by(email=email).first()
    if user:
        return user

    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def make_summary(category, zone):
    category_text = category.replace("_", " ")
    return f"Synthetic {category_text} report in {zone} for hotspot analysis."


def main():
    random.seed(20260703)
    app = create_app("development")

    with app.app_context():
        officer = ensure_user("officer@crimewatch.zw",   "officer",   "Officer1234!")
        ensure_user("admin@crimewatch.zw",               "admin",     "Admin1234!")
        # UI demo login users (match the frontend quick-access buttons)
        ensure_user("officer@harare.gov.zw",             "officer",   "password123")
        ensure_user("community@harare.gov.zw",           "community", "password123")

        db.session.query(Incident).filter(
            Incident.raw_text.like("Synthetic Harare GIS seed:%")
        ).delete(synchronize_session=False)

        now = datetime.now(timezone.utc)
        total = 0

        for zone in HARARE_HOTSPOT_ZONES:
            for index in range(zone["n_incidents"]):
                lat, lng = random_point(zone["center"], zone["radius_deg"])
                category = random.choice(zone["incident_types"])
                severity = random.choice(zone["severity_weights"])
                days_ago = random.randint(0, 89)

                incident = Incident(
                    raw_text=(
                        f"Synthetic Harare GIS seed: {category.replace('_', ' ')} "
                        f"reported near {zone['name']} #{index + 1}"
                    ),
                    language_detected="en",
                    category=category,
                    severity=severity,
                    triage_confidence=round(random.uniform(0.72, 0.96), 2),
                    triage_summary=make_summary(category, zone["name"]),
                    raw_gemini_response=None,
                    status="TRIAGED",
                    location=from_shape(Point(lng, lat), srid=4326),
                    location_description=f"{zone['name']}, Harare",
                    reported_by_id=officer.id,
                    created_at=now - timedelta(days=days_ago, hours=random.randint(0, 23)),
                )
                db.session.add(incident)
                total += 1

        db.session.commit()
        print(f"Seeded {total} incidents across {len(HARARE_HOTSPOT_ZONES)} Harare zones")


if __name__ == "__main__":
    main()
