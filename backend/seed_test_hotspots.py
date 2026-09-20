"""
Seed test hotspots for multi-vehicle routing testing.
Creates sample hotspots in the Harare area.
"""
from datetime import datetime, timezone
from app import create_app, db
from app.models.models import Hotspot
import uuid

app = create_app()

with app.app_context():
    # Check if hotspots already exist
    existing_count = db.session.query(Hotspot).count()
    if existing_count > 0:
        print(f"Hotspots already exist ({existing_count} found). Skipping seed.")
        exit(0)
    
    # Create test hotspots in Harare area
    test_hotspots = [
        {
            "hotspot_id": str(uuid.uuid4()),
            "lat": -17.8292,
            "lng": 31.0522,
            "dominant_category": "Theft",
            "incident_count": 15,
            "risk_score": 0.85,
            "status": "active",
            "consecutive_misses": 0,
            "first_detected_at": datetime.now(timezone.utc),
            "last_matched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "hotspot_id": str(uuid.uuid4()),
            "lat": -17.8252,
            "lng": 31.0475,
            "dominant_category": "Robbery",
            "incident_count": 12,
            "risk_score": 0.78,
            "status": "active",
            "consecutive_misses": 0,
            "first_detected_at": datetime.now(timezone.utc),
            "last_matched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "hotspot_id": str(uuid.uuid4()),
            "lat": -17.8189,
            "lng": 31.0433,
            "dominant_category": "Assault",
            "incident_count": 8,
            "risk_score": 0.65,
            "status": "active",
            "consecutive_misses": 0,
            "first_detected_at": datetime.now(timezone.utc),
            "last_matched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "hotspot_id": str(uuid.uuid4()),
            "lat": -17.8320,
            "lng": 31.0550,
            "dominant_category": "Burglary",
            "incident_count": 10,
            "risk_score": 0.72,
            "status": "active",
            "consecutive_misses": 0,
            "first_detected_at": datetime.now(timezone.utc),
            "last_matched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "hotspot_id": str(uuid.uuid4()),
            "lat": -17.8210,
            "lng": 31.0480,
            "dominant_category": "Vehicle Theft",
            "incident_count": 6,
            "risk_score": 0.58,
            "status": "emerging",
            "consecutive_misses": 0,
            "first_detected_at": datetime.now(timezone.utc),
            "last_matched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "hotspot_id": str(uuid.uuid4()),
            "lat": -17.8280,
            "lng": 31.0500,
            "dominant_category": "Fraud",
            "incident_count": 4,
            "risk_score": 0.45,
            "status": "emerging",
            "consecutive_misses": 0,
            "first_detected_at": datetime.now(timezone.utc),
            "last_matched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "hotspot_id": str(uuid.uuid4()),
            "lat": -17.8190,
            "lng": 31.0440,
            "dominant_category": "Vandalism",
            "incident_count": 7,
            "risk_score": 0.52,
            "status": "emerging",
            "consecutive_misses": 0,
            "first_detected_at": datetime.now(timezone.utc),
            "last_matched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "hotspot_id": str(uuid.uuid4()),
            "lat": -17.8300,
            "lng": 31.0530,
            "dominant_category": "Drug Activity",
            "incident_count": 9,
            "risk_score": 0.68,
            "status": "active",
            "consecutive_misses": 0,
            "first_detected_at": datetime.now(timezone.utc),
            "last_matched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    for hotspot_data in test_hotspots:
        hotspot = Hotspot(**hotspot_data)
        db.session.add(hotspot)
    
    db.session.commit()
    print(f"Successfully seeded {len(test_hotspots)} test hotspots")
    print("Hotspot IDs:")
    for hotspot_data in test_hotspots:
        print(f"  - {hotspot_data['hotspot_id']}")
