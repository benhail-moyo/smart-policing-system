"""
Unit tests for geographic partitioning module.
Tests edge cases for multi-vehicle hotspot partitioning.
"""
import pytest
from app.services.routing.partitioning import HotspotPartitioner, PartitionResult


class TestHotspotPartitioner:
    """Test geographic partitioning for multi-vehicle routing."""
    
    def test_n1_returns_single_group(self):
        """Test that N=1 returns all hotspots as a single group without KMeans."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8300, 31.0530),
            (-17.8310, 31.0540)
        ]
        
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=1)
        
        assert len(result.vehicle_groups) == 1
        assert len(result.vehicle_groups[0]) == 3
        assert result.fallback_used is False
        assert result.partition_sizes == [3]
        assert len(result.vehicle_assignments) == 3
    
    def test_n_zero_raises_value_error(self):
        """Test that N <= 0 raises ValueError."""
        hotspots = [(-17.8292, 31.0522)]
        partitioner = HotspotPartitioner()
        
        with pytest.raises(ValueError, match="vehicle_count must be positive"):
            partitioner.partition_hotspots(hotspots, vehicle_count=0)
        
        with pytest.raises(ValueError, match="vehicle_count must be positive"):
            partitioner.partition_hotspots(hotspots, vehicle_count=-1)
    
    def test_empty_hotspots_returns_empty_groups(self):
        """Test that empty hotspots list returns empty groups."""
        partitioner = HotspotPartitioner()
        result = partitioner.partition_hotspots([], vehicle_count=3)
        
        assert len(result.vehicle_groups) == 3
        assert all(len(group) == 0 for group in result.vehicle_groups)
        assert result.partition_sizes == [0, 0, 0]
        assert len(result.vehicle_assignments) == 0
    
    def test_n_greater_than_hotspot_count(self):
        """Test that N >= hotspot_count uses round-robin assignment."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8300, 31.0530)
        ]
        
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=5)
        
        assert len(result.vehicle_groups) == 5
        assert result.fallback_used is False  # Expected behavior, not error fallback
        assert sum(result.partition_sizes) == 2
        # Some vehicles should have 0 hotspots
        assert result.partition_sizes.count(0) >= 3
    
    def test_duplicate_coordinates_handling(self):
        """Test that duplicate coordinates are handled gracefully."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8292, 31.0522),  # Duplicate
            (-17.8292, 31.0522),  # Duplicate
            (-17.8300, 31.0530)
        ]
        
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        # Should handle duplicates gracefully (KMeans may or may not trigger fallback)
        assert len(result.vehicle_groups) == 2
        assert sum(result.partition_sizes) == 4
        # All hotspots should still be assigned
        assert all(len(group) >= 0 for group in result.vehicle_groups)
    
    def test_every_hotspot_assigned_exactly_once(self):
        """Test that every hotspot is assigned to exactly one vehicle."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8300, 31.0530),
            (-17.8310, 31.0540),
            (-17.8320, 31.0550),
            (-17.8330, 31.0560)
        ]
        
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        # Check total assignments
        total_assigned = sum(len(group) for group in result.vehicle_groups)
        assert total_assigned == 5
        
        # Check each hotspot appears exactly once
        all_assigned_hotspots = []
        for group in result.vehicle_groups:
            all_assigned_hotspots.extend(group)
        
        # Check no duplicates
        assert len(all_assigned_hotspots) == len(set(all_assigned_hotspots))
        
        # Check all original hotspots are present
        assert set(all_assigned_hotspots) == set(hotspots)
    
    def test_no_duplicate_assignments_across_vehicles(self):
        """Test that no hotspot is assigned to multiple vehicles."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8300, 31.0530),
            (-17.8310, 31.0540)
        ]
        
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        # Check vehicle_assignments mapping
        assigned_vehicles = set(result.vehicle_assignments.values())
        assert len(assigned_vehicles) <= 2  # At most 2 vehicles
        
        # Each hotspot index should map to exactly one vehicle
        assert len(result.vehicle_assignments) == 3
    
    def test_multi_depot_initialization(self):
        """Test that multi-depot initialization works correctly."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8300, 31.0530),
            (-17.8310, 31.0540),
            (-17.8320, 31.0550)
        ]
        
        depot_locations = [
            (-17.8280, 31.0510),  # Vehicle 0 depot
            (-17.8330, 31.0560)   # Vehicle 1 depot
        ]
        
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(
            hotspots, 
            vehicle_count=2,
            depot_locations=depot_locations
        )
        
        assert len(result.vehicle_groups) == 2
        assert result.fallback_used is False
        assert sum(result.partition_sizes) == 4
    
    def test_depot_locations_length_mismatch(self):
        """Test that depot_locations length must match vehicle_count."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8300, 31.0530),
            (-17.8310, 31.0540)
        ]
        depot_locations = [(-17.8280, 31.0510)]  # Only 1 depot for 2 vehicles
        
        partitioner = HotspotPartitioner()
        
        with pytest.raises(ValueError, match="depot_locations length.*must match vehicle_count"):
            partitioner.partition_hotspots(
                hotspots, 
                vehicle_count=2,
                depot_locations=depot_locations
            )
    
    def test_partition_sizes_recorded_correctly(self):
        """Test that partition_sizes are recorded correctly."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8300, 31.0530),
            (-17.8310, 31.0540),
            (-17.8320, 31.0550),
            (-17.8330, 31.0560)
        ]
        
        partitioner = HotspotPartitioner(random_state=42)
        result = partitioner.partition_hotspots(hotspots, vehicle_count=2)
        
        # Check partition_sizes matches actual group sizes
        expected_sizes = [len(group) for group in result.vehicle_groups]
        assert result.partition_sizes == expected_sizes
    
    def test_realistic_harare_data_partitioning(self):
        """Test partitioning with realistic Harare coordinates."""
        # Simulated hotspot coordinates around Harare
        hotspots = [
            (-17.8292, 31.0522),  # CBD area
            (-17.8300, 31.0530),
            (-17.8310, 31.0540),
            (-17.8400, 31.0600),  # Northern suburbs
            (-17.8410, 31.0610),
            (-17.8500, 31.0700),  # Eastern areas
            (-17.8510, 31.0710),
            (-17.8200, 31.0400),  # Western areas
            (-17.8210, 31.0410),
        ]
        
        partitioner = HotspotPartitioner(random_state=42)
        
        # Test with different vehicle counts
        for vehicle_count in [2, 3, 5]:
            result = partitioner.partition_hotspots(hotspots, vehicle_count)
            
            assert len(result.vehicle_groups) == vehicle_count
            assert sum(result.partition_sizes) == len(hotspots)
            assert all(size >= 0 for size in result.partition_sizes)
            
            # Log partition sizes for validation
            print(f"N={vehicle_count}: partition_sizes={result.partition_sizes}")
    
    def test_random_state_reproducibility(self):
        """Test that random_state produces reproducible results."""
        hotspots = [
            (-17.8292, 31.0522),
            (-17.8300, 31.0530),
            (-17.8310, 31.0540),
            (-17.8320, 31.0550)
        ]
        
        partitioner1 = HotspotPartitioner(random_state=42)
        result1 = partitioner1.partition_hotspots(hotspots, vehicle_count=2)
        
        partitioner2 = HotspotPartitioner(random_state=42)
        result2 = partitioner2.partition_hotspots(hotspots, vehicle_count=2)
        
        # Results should be identical
        assert result1.partition_sizes == result2.partition_sizes
        assert result1.vehicle_assignments == result2.vehicle_assignments