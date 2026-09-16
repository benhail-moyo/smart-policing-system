#!/usr/bin/env python
"""Test N=1 regression for multi-vehicle routing."""
from app import create_app
from app.models.models import Hotspot
from app.services.routing.route_engine import route_engine
from datetime import datetime, timezone
import uuid
import json

app = create_app()

with app.app_context():
    # Check if we have hotspots in the database
    hotspots = Hotspot.query.all()
    print(f"Found {len(hotspots)} hotspots in database")
    
    if len(hotspots) < 3:
        print("Not enough hotspots for testing. Creating test hotspots...")
        from app import db
        test_hotspots = [
            Hotspot(
                hotspot_id=str(uuid.uuid4()),
                lat=-17.8292 + (i * 0.01),
                lng=31.0522 + (i * 0.01),
                risk_score=0.8,
                status='active',
                incident_count=5,
                first_detected_at=datetime.now(timezone.utc),
                dominant_category='Theft'
            )
            for i in range(5)
        ]
        for hotspot in test_hotspots:
            db.session.add(hotspot)
        db.session.commit()
        hotspots = Hotspot.query.all()
        print(f"Created {len(hotspots)} test hotspots")
    
    # Get hotspot IDs
    hotspot_ids = [str(h.hotspot_id) for h in hotspots[:5]]
    print(f"Testing with hotspot IDs: {hotspot_ids}")
    
    # Test 1: Single-vehicle optimization (existing method)
    print("\n=== Test 1: Single-vehicle optimization (existing method) ===")
    single_result = route_engine.optimize(
        hotspot_ids,
        algorithm='both',
        start_location=(-17.8292, 31.0522),
        save_to_db=False
    )
    
    print(f"Single-vehicle result count: {len(single_result)}")
    for result in single_result:
        print(f"  {result.algorithm}: {result.total_distance_km} km, {result.hotspots_covered} hotspots")
    
    # Test 2: Multi-vehicle optimization with N=1 (new method)
    print("\n=== Test 2: Multi-vehicle optimization with N=1 (new method) ===")
    multi_result = route_engine.optimize_multi_vehicle(
        hotspot_ids,
        vehicle_count=1,
        algorithm='both',
        start_location=(-17.8292, 31.0522),
        save_to_db=False
    )
    
    print(f"Multi-vehicle result vehicle_count: {multi_result['vehicle_count']}")
    print(f"Multi-vehicle result route count: {len(multi_result['routes'])}")
    print(f"Partition metadata: {multi_result['partition_metadata']}")
    
    # Compare results
    print("\n=== Regression Check ===")
    if len(single_result) == len(multi_result['routes']):
        print(f"[PASS] Same number of results: {len(single_result)}")
    else:
        print(f"[FAIL] Different number of results: single={len(single_result)}, multi={len(multi_result['routes'])}")
    
    # Check each algorithm's results
    for single, multi in zip(single_result, multi_result['routes']):
        print(f"\nAlgorithm: {single.algorithm}")
        
        # Check distance
        if abs(single.total_distance_km - multi['total_distance_km']) < 0.001:
            print(f"  [PASS] Distance matches: {single.total_distance_km} km")
        else:
            print(f"  [FAIL] Distance mismatch: single={single.total_distance_km}, multi={multi['total_distance_km']}")
        
        # Check hotspots covered
        if single.hotspots_covered == multi['hotspots_covered']:
            print(f"  [PASS] Hotspots covered matches: {single.hotspots_covered}")
        else:
            print(f"  [FAIL] Hotspots covered mismatch: single={single.hotspots_covered}, multi={multi['hotspots_covered']}")
        
        # Check hotspot IDs
        if set(single.hotspot_ids) == set(multi['hotspot_ids']):
            print(f"  [PASS] Hotspot IDs match")
        else:
            print(f"  [FAIL] Hotspot IDs mismatch")
            print(f"    Single: {single.hotspot_ids}")
            print(f"    Multi: {multi['hotspot_ids']}")
    
    print("\n=== N=1 Regression Test Complete ===")