#!/usr/bin/env python
"""Test multi-vehicle routing with N>1 scenarios."""
from app import create_app
from app.models.models import Hotspot
from app.services.routing.route_engine import route_engine
from datetime import datetime, timezone
import uuid

app = create_app()

with app.app_context():
    # Get hotspots
    hotspots = Hotspot.query.all()
    print(f"Found {len(hotspots)} hotspots in database")
    
    if len(hotspots) < 10:
        print("Not enough hotspots for testing. Creating more test hotspots...")
        from app import db
        # Create hotspots distributed across Harare area for better partitioning
        additional_hotspots = []
        base_lat = -17.8292
        base_lng = 31.0522
        
        # Create clusters in different areas
        for cluster_idx in range(3):
            cluster_lat = base_lat + (cluster_idx * 0.02)
            cluster_lng = base_lng + (cluster_idx * 0.02)
            
            for i in range(5):
                hotspot = Hotspot(
                    hotspot_id=str(uuid.uuid4()),
                    lat=cluster_lat + (i * 0.005),
                    lng=cluster_lng + (i * 0.005),
                    risk_score=0.6 + (i * 0.05),
                    status='active',
                    incident_count=3 + i,
                    first_detected_at=datetime.now(timezone.utc),
                    last_matched_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    dominant_category='Robbery' if i % 2 == 0 else 'Theft'
                )
                additional_hotspots.append(hotspot)
        
        for hotspot in additional_hotspots:
            db.session.add(hotspot)
        db.session.commit()
        hotspots = Hotspot.query.all()
        print(f"Created additional hotspots. Total: {len(hotspots)}")
    
    # Get hotspot IDs for testing - use more distributed hotspots
    # Use the same hotspots that the partitioning debug script uses
    test_hotspots = hotspots[:15]
    hotspot_ids = [str(h.hotspot_id) for h in test_hotspots]
    print(f"Testing with {len(hotspot_ids)} hotspots")
    print(f"Hotspot IDs: {[hid[:8] for hid in hotspot_ids]}")
    
    # Test different vehicle counts
    vehicle_counts = [2, 3, 5]
    
    for vehicle_count in vehicle_counts:
        print(f"\n{'='*60}")
        print(f"Testing with {vehicle_count} vehicles")
        print(f"{'='*60}")
        
        try:
            result = route_engine.optimize_multi_vehicle(
                hotspot_ids,
                vehicle_count=vehicle_count,
                algorithm='both',
                start_location=(-17.8292, 31.0522),
                save_to_db=False
            )
            
            print(f"Generation ID: {result['generation_id']}")
            print(f"Vehicle count: {result['vehicle_count']}")
            print(f"Total routes: {len(result['routes'])}")
            print(f"Partition sizes: {result['partition_metadata']['partition_sizes']}")
            print(f"Fallback used: {result['partition_metadata']['fallback_used']}")
            print(f"Load imbalance: {result['partition_metadata']['load_imbalance']}")
            
            # Analyze routes per vehicle
            print(f"\nRoute details:")
            for route in result['routes']:
                vehicle_id = route['vehicle_id']
                algorithm = route['algorithm']
                distance = route['total_distance_km']
                hotspots = route['hotspots_covered']
                print(f"  Vehicle {vehicle_id} ({algorithm}): {distance:.3f} km, {hotspots} hotspots")
            
            # Validate partition integrity - check per algorithm (skip empty routes)
            for algorithm in ['dijkstra', 'genetic']:
                algorithm_routes = [r for r in result['routes'] if r['algorithm'] == algorithm and not r.get('empty_route')]
                all_hotspot_ids = []
                for route in algorithm_routes:
                    all_hotspot_ids.extend(route['hotspot_ids'])
                
                # Check for duplicates within this algorithm
                if len(all_hotspot_ids) == len(set(all_hotspot_ids)):
                    print(f"[PASS] No duplicate hotspot assignments for {algorithm}")
                else:
                    print(f"[FAIL] Duplicate hotspot assignments detected for {algorithm}")
                
                # Check all hotspots assigned for this algorithm
                if set(all_hotspot_ids) == set(hotspot_ids):
                    print(f"[PASS] All hotspots assigned to vehicles for {algorithm}")
                else:
                    print(f"[FAIL] Some hotspots not assigned for {algorithm}")
                    print(f"  Expected: {set(hotspot_ids)}")
                    print(f"  Got: {set(all_hotspot_ids)}")
                
        except Exception as e:
            print(f"[ERROR] Test failed for vehicle_count={vehicle_count}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Multi-vehicle scenario testing complete")
    print(f"{'='*60}")