#!/usr/bin/env python3
"""
Seed script for Harare synthetic incidents.

This is a minimal placeholder so developers can run a quick seed.
Run: python backend/scripts/seed_harare_incidents.py
"""
import random
from datetime import datetime, timedelta

from app import create_app, db
from app.models.models import User, Incident
from geoalchemy2.shape import from_shape
from shapely.geometry import Point


def random_point(center, radius_deg):
    lat_c, lng_c = center
    return (
        lat_c + random.uniform(-radius_deg, radius_deg),
        lng_c + random.uniform(-radius_deg, radius_deg),
    )


def main():
    app = create_app('development')
    with app.app_context():
        # create users if not exists
        if not db.session.query(User).filter_by(email='admin@crimewatch.zw').first():
            admin = User(email='admin@crimewatch.zw', role='admin')
            admin.set_password('Admin1234!')
            db.session.add(admin)

        # create a few incidents around Harare CBD as an example
        HARARE_CENTERS = [(-17.8292, 31.0522), (-17.8677, 31.0359), (-17.89, 31.01)]
        categories = ['robbery', 'assault', 'theft', 'suspicious_activity']

        for i in range(50):
            center = random.choice(HARARE_CENTERS)
            lat, lng = random_point(center, 0.012)
            inc = Incident(
                raw_text=f"Synthetic incident {i}",
                language_detected='en',
                category=random.choice(categories),
                severity=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                triage_confidence=random.random(),
                triage_summary='Synthetic seed data',
                status='TRIAGED',
                location=from_shape(Point(lng, lat), srid=4326),
                location_description='Synthetic Harare',
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            )
            db.session.add(inc)

        db.session.commit()
        print('Seeded synthetic incidents and users (if missing).')


if __name__ == '__main__':
    main()
