#!/usr/bin/env python
"""Debug partitioning within route engine context."""
from app import create_app
from app.models.models import Hotspot
from app.services.routing.route_engine import route_engine

app = create_app()

with app.app_context():
    hotspots = Hotspot.query.all()
    print(f"Total hotspots: {len(hotspots)}")
    
    # Use the same hotspots as test_multi_vehicle_scenarios
    test_hotspots = hotspots[:15]
    hotspot_ids = [str(h.hotspot_id) for h in test_hotspots]
    print(f"Testing with {len(hotspot_ids)} hotspots")
    
    # Extract centroids the same way route_engine does
    hotspot_centroids = route_engine._hotspots_to_waypoints(test_hotspots)
    print(f"Extracted {len(hotspot_centroids)} centroids")
    print(f"First few centroids: {hotspot_centroids[:3]}")
    
    # Now test partitioning directly 
    from app.services.routing.partitioning import HotspotPartitioner
    partitioner = HotspotPartitioner(random_state=42)
    
    for vehicle_count in [2, 3]:
        print(f"\n{'='*60}")
        print(f"Partitioning for {vehicle_count} vehicles (route_engine context)")
        print(f"{'='*60}")
        
        result = partitioner.partition_hotspots(hotspot_centroids, vehicle_count)
        
        print(f"Partition sizes: {result.partition_sizes}")
        print(f"Fallback used: {result.fallback_used}")
        print(f"Total groups: {len(result.vehicle_groups)}")
        
        for vehicle_id, group in enumerate(result.vehicle_groups):
            print(f"  Vehicle {vehicle_id}: {len(group)} hotspots")