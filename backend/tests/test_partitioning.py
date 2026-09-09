"""
Unit tests for hotspot partitioning module.
Tests edge cases and validation requirements from multi-vehicle routing phase.
"""
import pytest
import numpy as np
from app.services.routing.partitioning import HotspotPartitioner, PartitionResult


class TestHotspotPartitioner:
    """Test suite for HotspotPartitioner edge cases and correctness."""
    
    def test_n_equals_one_returns_single_group(self):
        """Test that N=1 returns all hotspots as a single group without KMeans."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8252, 31.0475),
            (-17.8189, 31.0433),
            (-17.8150, 31.0500)
        ]
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=1)
        
        assert len(result.vehicle_groups) == 1
        assert len(result.vehicle_groups[0]) == len(hotspots)
        assert result.vehicle_groups[0] == hotspots
        assert result.fallback_used is False
        assert result.partition_sizes == [4]
    
    def test_n_less_than_or_equal_zero_raises_error(self):
        """Test that N <= 0 raises ValueError."""
        hotspots = [(-17.8292, 31.0522), (-17.8252, 31.0475)]
        partitioner = HotspotPartitioner()
        
        with pytest.raises(ValueError, match="vehicle_count must be positive"):
            partitioner.partition_hotspots(hotspots, vehicle_count=0)
        
        with pytest.raises(ValueError, match="vehicle_count must be positive"):
            partitioner.partition_hotspots(hotspots, vehicle_count=-1)
    
    def test_empty_hotspots_returns_empty_groups(self):
        """Test that empty hotspot list returns empty groups for all vehicles."""
        partitioner = HotspotPartitioner()
        result = partitioner.partition_hotspots([], vehicle_count=3)
        
        assert len(result.vehicle_groups) == 3
        assert all(len(group) == 0 for group in result.vehicle_groups)
        assert result.partition_sizes == [0, 0, 0]
        assert len(result.vehicle_assignments) == 0
    
    def test_n_greater_than_or_equal_hotspot_count(self):
        """Test that N >= hotspot_count handles gracefully with round-robin."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8252, 31.0475)
        ]
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=5)
        
        assert len(result.vehicle_groups) == 5
        # Should use round-robin, so first 2 vehicles get 1 hotspot each
        assert result.partition_sizes == [1, 1, 0, 0, 0]
        # Verify no duplicate assignments
        assert len(result.vehicle_assignments) == len(hotspots)
    
    def test_every_hotspot_assigned_exactly_once(self):
        """Test that every hotspot is assigned to exactly one vehicle."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8252, 31.0475),
            (-17.8189, 31.0433),
            (-17.8150, 31.0500),
            (-17.8200, 31.0450)
        ]
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        # Total hotspots across all groups should equal input
        total_assigned = sum(len(group) for group in result.vehicle_groups)
        assert total_assigned == len(hotspots)
        
        # Verify each hotspot appears exactly once
        all_assigned = []
        for group in result.vehicle_groups:
            all_assigned.extend(group)
        
        # Sort for comparison
        all_assigned_sorted = sorted(all_assigned)
        hotspots_sorted = sorted(hotspots)
        assert all_assigned_sorted == hotspots_sorted
    
    def test_no_duplicate_assignments_across_vehicles(self):
        """Test that no hotspot is assigned to multiple vehicles."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8252, 31.0475),
            (-17.8189, 31.0433)
        ]
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        # Check vehicle_assignments has unique values
        assignment_values = list(result.vehicle_assignments.values())
        assert len(assignment_values) == len(set(assignment_values))
    
    def test_degenerate_kmeans_triggers_fallback(self):
        """Test that degenerate KMeans (duplicate coordinates) triggers round-robin fallback."""
        # All hotspots at same location - should trigger fallback
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8292, 31.0522),
            (-17.8292, 31.0522),
            (-17.8292, 31.0522)
        ]
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        # Should fall back to round-robin
        assert result.fallback_used is True
        # Should still partition correctly
        assert sum(len(group) for group in result.vehicle_groups) == len(hotspots)
    
    def test_multi_depot_with_correct_depot_count(self):
        """Test multi-depot partitioning with correct depot location count."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8252, 31.0475),
            (-17.8189, 31.0433)
        ]
        depot_locations = [
            (-17.8300, 31.0530),  # Vehicle 1 depot
            (-17.8200, 31.0440)   # Vehicle 2 depot
        ]
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(
            hotspots,
            vehicle_count=2,
            depot_locations=depot_locations
        )
        
        assert len(result.vehicle_groups) == 2
        assert result.fallback_used is False
    
    def test_multi_depot_with_incorrect_depot_count_raises_error(self):
        """Test that mismatched depot location count raises ValueError."""
        hotspots = [(-17.8292, 31.0522), (-17.8252, 31.0475)]
        depot_locations = [(-17.8300, 31.0530)]  # Only 1 depot for 2 vehicles
        
        partitioner = HotspotPartitioner()
        with pytest.raises(ValueError, match="depot_locations length.*must match vehicle_count"):
            partitioner.partition_hotspots(
                hotspots,
                vehicle_count=2,
                depot_locations=depot_locations
            )
    
    def test_single_depot_geographic_clustering(self):
        """Test single-depot scenario (geographic clustering only)."""
        hotspots = [
            (-17.8292, 31.0522),  # Group A
            (-17.8280, 31.0510),  # Group A
            (-17.8150, 31.0400),  # Group B
            (-17.8140, 31.0390),  # Group B
        ]
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        assert len(result.vehicle_groups) == 2
        assert result.fallback_used is False
        # Geographic clustering should group nearby points
        total_assigned = sum(len(group) for group in result.vehicle_groups)
        assert total_assigned == len(hotspots)
    
    def test_partition_sizes_reported_correctly(self):
        """Test that partition_sizes accurately reflects group sizes."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8252, 31.0475),
            (-17.8189, 31.0433),
            (-17.8150, 31.0500),
            (-17.8200, 31.0450)
        ]
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        # Verify partition_sizes matches actual group sizes
        expected_sizes = [len(group) for group in result.vehicle_groups]
        assert result.partition_sizes == expected_sizes
    
    def test_reproducibility_with_random_state(self):
        """Test that same random_state produces identical results."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8252, 31.0475),
            (-17.8189, 31.0433),
            (-17.8150, 31.0500)
        ]
        
        partitioner1 = HotspotPartitioner(random_state=42)
        result1 = partitioner1.partition_hotspots(hotspots, vehicle_count=2)
        
        partitioner2 = HotspotPartitioner(random_state=42)
        result2 = partitioner2.partition_hotspots(hotspots, vehicle_count=2)
        
        # Results should be identical
        assert result1.partition_sizes == result2.partition_sizes
        assert result1.vehicle_assignments == result2.vehicle_assignments
        assert result1.fallback_used == result2.fallback_used


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
