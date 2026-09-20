#!/usr/bin/env python
"""Debug partitioning behavior."""
from app import create_app
from app.models.models import Hotspot
from app.services.routing.partitioning import HotspotPartitioner

app = create_app()

with app.app_context():
    hotspots = Hotspot.query.all()
    print(f"Total hotspots: {len(hotspots)}")
    
    # Get centroids
    hotspot_centroids = [(h.lat, h.lng) for h in hotspots[:15]]
    print(f"Testing with {len(hotspot_centroids)} hotspots")
    
    # Test partitioning
    partitioner = HotspotPartitioner(random_state=42)
    
    for vehicle_count in [2, 3, 5]:
        print(f"\n{'='*60}")
        print(f"Partitioning for {vehicle_count} vehicles")
        print(f"{'='*60}")
        
        result = partitioner.partition_hotspots(hotspot_centroids, vehicle_count)
        
        print(f"Partition sizes: {result.partition_sizes}")
        print(f"Fallback used: {result.fallback_used}")
        print(f"Load imbalance: {(max(result.partition_sizes) - min(result.partition_sizes)) / max(len(hotspot_centroids), 1):.3f}")
        
        print(f"\nVehicle assignments:")
        for vehicle_id, group in enumerate(result.vehicle_groups):
            print(f"  Vehicle {vehicle_id}: {len(group)} hotspots")
            if group:
                print(f"    First hotspot: {group[0]}")
                print(f"    Last hotspot: {group[-1]}")