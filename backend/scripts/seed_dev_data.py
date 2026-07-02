#!/usr/bin/env python3
"""
Seed development users and a small set of incidents.
Run: python backend/scripts/seed_dev_data.py
"""
import random
from datetime import datetime

from app import create_app, db
from app.models.models import User, Incident
from geoalchemy2.shape import from_shape
from shapely.geometry import Point


def main():
    app = create_app('development')
    with app.app_context():
        # Users
        users = [
            ('admin@crimewatch.zw', 'Admin1234!', 'admin'),
            ('officer@crimewatch.zw', 'Officer1234!', 'officer'),
            ('community@crimewatch.zw', 'Community1234!', 'community'),
        ]
        for email, pwd, role in users:
            if not db.session.query(User).filter_by(email=email).first():
                u = User(email=email, role=role)
                u.set_password(pwd)
                db.session.add(u)

        # Small number of incidents
        centers = [(-17.8292, 31.0522), (-17.8677, 31.0359), (-17.89, 31.01)]
        cats = ['robbery', 'assault', 'theft', 'suspicious_activity']
        for i in range(20):
            lat = centers[i % len(centers)][0] + random.uniform(-0.01, 0.01)
            lng = centers[i % len(centers)][1] + random.uniform(-0.01, 0.01)
            inc = Incident(
                raw_text=f"Dev incident {i}",
                language_detected='en',
                category=random.choice(cats),
                severity=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                triage_confidence=round(random.random(), 2),
                triage_summary='Dev seed',
                status='TRIAGED',
                location=from_shape(Point(lng, lat), srid=4326),
                location_description='Dev seed',
                created_at=datetime.utcnow(),
            )
            db.session.add(inc)

        db.session.commit()
        print('Seeded dev users and incidents.')


if __name__ == '__main__':
    main()
