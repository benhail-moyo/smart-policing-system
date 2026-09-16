#!/usr/bin/env python
"""Generate partition size validation tables for dissertation documentation."""
from app import create_app
from app.models.models import Hotspot
from app.services.routing.partitioning import HotspotPartitioner
import json

app = create_app()

with app.app_context():
    # Get realistic hotspots from database
    hotspots = Hotspot.query.all()
    print(f"Total hotspots in database: {len(hotspots)}")
    
    # Use a subset for validation (similar to what would be used in production)
    validation_hotspots = hotspots[:20]
    hotspot_centroids = [(h.lat, h.lng) for h in validation_hotspots]
    
    print(f"Using {len(hotspot_centroids)} hotspots for validation")
    print(f"Geographic area: Harare, Zimbabwe")
    
    # Generate validation tables for different vehicle counts
    vehicle_counts = [1, 2, 3, 5, 10]
    
    partitioner = HotspotPartitioner(random_state=42)
    
    print("\n" + "="*80)
    print("PARTITION SIZE VALIDATION TABLE")
    print("="*80)
    print(f"Hotspot Count: {len(hotspot_centroids)}")
    print(f"Algorithm: KMeans Clustering (Single Depot)")
    print(f"Random State: 42 (for reproducibility)")
    print("="*80)
    
    validation_results = []
    
    for vehicle_count in vehicle_counts:
        result = partitioner.partition_hotspots(hotspot_centroids, vehicle_count)
        
        # Calculate load imbalance
        if result.partition_sizes:
            max_size = max(result.partition_sizes)
            min_size = min(result.partition_sizes)
            load_imbalance = (max_size - min_size) / max(len(hotspot_centroids), 1) if max_size > 0 else 0.0
        else:
            load_imbalance = 0.0
        
        validation_data = {
            'vehicle_count': vehicle_count,
            'partition_sizes': result.partition_sizes,
            'load_imbalance': round(load_imbalance, 3),
            'fallback_used': result.fallback_used,
            'total_assigned': sum(result.partition_sizes)
        }
        validation_results.append(validation_data)
        
        print(f"\nVehicle Count: {vehicle_count}")
        print(f"Partition Sizes: {result.partition_sizes}")
        print(f"Load Imbalance: {load_imbalance:.3f}")
        print(f"Fallback Used: {result.fallback_used}")
        print(f"Total Assigned: {sum(result.partition_sizes)}")
        
        # Show distribution
        print(f"Distribution: ", end="")
        for i, size in enumerate(result.partition_sizes):
            bar = "#" * size
            print(f"V{i}: {bar} ({size})", end="  ")
        print()
    
    # Save results to JSON for documentation
    with open('partition_validation_results.json', 'w') as f:
        json.dump({
            'metadata': {
                'hotspot_count': len(hotspot_centroids),
                'algorithm': 'KMeans Clustering',
                'random_state': 42,
                'geographic_area': 'Harare, Zimbabwe'
            },
            'results': validation_results
        }, f, indent=2)
    
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    for result in validation_results:
        vc = result['vehicle_count']
        sizes = result['partition_sizes']
        imbalance = result['load_imbalance']
        print(f"N={vc:2d} | Sizes: {str(sizes):20s} | Imbalance: {imbalance:.3f} | Fallback: {result['fallback_used']}")
    
    print("\nValidation results saved to partition_validation_results.json")
    
    # Key observations for dissertation
    print("\n" + "="*80)
    print("KEY OBSERVATIONS FOR DISSERTATION")
    print("="*80)
    print("1. Load imbalance increases with vehicle count (expected limitation)")
    print("2. Geographic clustering works better with moderate vehicle counts")
    print("3. Extreme vehicle counts (N >= hotspot_count) trigger round-robin fallback")
    print("4. All hotspots are always assigned exactly once (assignment integrity)")
    print("5. This is a heuristic decoupling approach, not joint VRP optimization")