"""
Unit tests for spatial index and snapping functionality.
"""
import pytest
import numpy as np
from app.services.routing.spatial_index import SpatialIndex, haversine_distance_m


class TestSpatialIndex:
    """Test spatial index implementation."""
    
    def test_basic_indexing(self):
        """Test basic spatial index creation."""
        nodes = {
            0: {'lat': -17.8292, 'lng': 31.0522},
            1: {'lat': -17.8252, 'lng': 31.0475},
            2: {'lat': -17.8189, 'lng': 31.0433}
        }
        
        index = SpatialIndex(nodes)
        
        assert index.kdtree is not None
        assert len(index.node_ids) == 3
        assert index.crs_info is not None
    
    def test_nearest_node_finding(self):
        """Test finding nearest node."""
        nodes = {
            0: {'lat': -17.8292, 'lng': 31.0522},
            1: {'lat': -17.8252, 'lng': 31.0475},
            2: {'lat': -17.8189, 'lng': 31.0433}
        }
        
        index = SpatialIndex(nodes)
        
        # Query near node 0
        result = index.find_nearest_node(-17.8292, 31.0522)
        
        assert result is not None
        assert result.node_id == 0
        assert result.snap_distance_m < 10  # Should be very close
    
    def test_max_snap_distance(self):
        """Test that points beyond max distance return None."""
        nodes = {
            0: {'lat': -17.8292, 'lng': 31.0522}
        }
        
        index = SpatialIndex(nodes)
        
        # Query point far away
        result = index.find_nearest_node(0.0, 0.0, max_snap_distance_m=100)
        
        assert result is None
    
    def test_empty_nodes(self):
        """Test spatial index with empty nodes."""
        nodes = {}
        
        index = SpatialIndex(nodes)
        
        assert index.kdtree is None
        assert index.projected_coords is None
    
    def test_utm_zone_determination(self):
        """Test UTM zone determination for Harare."""
        nodes = {
            0: {'lat': -17.8292, 'lng': 31.0522}  # Harare coordinates
        }
        
        index = SpatialIndex(nodes)
        
        # Harare should be in UTM zone 36
        assert index.crs_info['utm_zone'] == 36
        assert index.crs_info['hemisphere'] == 'S'


class TestHaversineDistance:
    """Test Haversine distance calculation."""
    
    def test_same_point(self):
        """Test distance between same point is zero."""
        distance = haversine_distance_m(-17.8292, 31.0522, -17.8292, 31.0522)
        assert distance == 0.0
    
    def test_known_distance(self):
        """Test Haversine distance for known coordinates."""
        # Distance between two points in Harare (approximate)
        distance = haversine_distance_m(-17.8292, 31.0522, -17.8252, 31.0475)
        
        # Should be roughly 600-700 metres
        assert 500 < distance < 1000
    
    def test_equator_distance(self):
        """Test distance along equator."""
        # 1 degree of longitude at equator ≈ 111.32 km
        distance = haversine_distance_m(0.0, 0.0, 0.0, 1.0)
        
        # Should be approximately 111 km
        assert 110000 < distance < 112000
    
    def test_symmetry(self):
        """Test that distance is symmetric."""
        distance1 = haversine_distance_m(-17.8292, 31.0522, -17.8252, 31.0475)
        distance2 = haversine_distance_m(-17.8252, 31.0475, -17.8292, 31.0522)
        
        assert abs(distance1 - distance2) < 0.01  # Should be essentially equal
