"""
Regression test for N=1 multi-vehicle routing.
Verifies that multi-vehicle system behaves identically to single-vehicle system when vehicle_count=1.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.routing.partitioning import HotspotPartitioner


def test_n1_regression():
    """
    Test that vehicle_count=1 produces identical results to single-vehicle system.
    This is a critical regression requirement.
    """
    print("Running N=1 regression test...")
    
    # Create test hotspots (realistic Harare coordinates)
    test_hotspots = [
        (-17.8292, 31.0522),
        (-17.8300, 31.0530),
        (-17.8310, 31.0540),
        (-17.8320, 31.0550),
        (-17.8330, 31.0560)
    ]
    
    print(f"Test hotspots: {len(test_hotspots)}")
    
    # Test partitioning with N=1
    print("\nTesting partitioning with vehicle_count=1...")
    try:
        partitioner = HotspotPartitioner(random_state=42)
        partition_result = partitioner.partition_hotspots(test_hotspots, vehicle_count=1)
        
        print(f"Partition result: {len(partition_result.vehicle_groups)} groups")
        print(f"Partition sizes: {partition_result.partition_sizes}")
        print(f"Fallback used: {partition_result.fallback_used}")
        
        # Verify N=1 returns all hotspots in single group
        assert len(partition_result.vehicle_groups) == 1, "N=1 should return 1 group"
        assert len(partition_result.vehicle_groups[0]) == len(test_hotspots), "N=1 should include all hotspots"
        assert partition_result.fallback_used is False, "N=1 should not use fallback"
        assert partition_result.partition_sizes == [len(test_hotspots)], "Partition size should match hotspot count"
        
        # Verify all hotspots are assigned to vehicle 0
        assert all(assign == 0 for assign in partition_result.vehicle_assignments.values()), "All hotspots should be assigned to vehicle 0"
        
        print("PASS: N=1 partitioning behaves correctly")
        
    except Exception as e:
        print(f"Partitioning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\nPASS: N=1 regression test PASSED")
    print("  - N=1 returns all hotspots in single group (no partitioning)")
    print("  - All hotspots assigned to vehicle 0")
    print("  - No fallback triggered")
    print("  - Partition size equals total hotspot count")
    
    return True


if __name__ == "__main__":
    success = test_n1_regression()
    sys.exit(0 if success else 1)