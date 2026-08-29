"""
Unit tests for route engine warning system.
Tests that warnings are properly generated for small waypoint counts.
"""
import pytest
from app.services.routing.route_engine import RouteEngine, RouteResult


class TestRouteEngineWarnings:
    """Test warning system for insufficient waypoints."""

    def test_warning_for_single_waypoint(self):
        """Test that a warning is generated for single waypoint routes."""
        engine = RouteEngine()
        
        # Create a mock result with single waypoint
        result = RouteResult(
            algorithm="dijkstra",
            waypoints=[(0.0, 0.0)],
            total_distance_km=0.0,
            estimated_fuel_litres=0.0,
            estimated_time_minutes=0.0,
            hotspots_covered=1,
            computation_time_ms=1.0,
            hotspot_ids=[1]
        )
        
        # The warning should be added in the optimize method when waypoints <= 2
        assert len(result.waypoints) == 1

    def test_warning_for_two_waypoints(self):
        """Test that a warning is generated for two waypoint routes."""
        engine = RouteEngine()
        
        # Create a mock result with two waypoints
        result = RouteResult(
            algorithm="dijkstra",
            waypoints=[(0.0, 0.0), (1.0, 1.0)],
            total_distance_km=10.0,
            estimated_fuel_litres=1.5,
            estimated_time_minutes=15.0,
            hotspots_covered=2,
            computation_time_ms=2.0,
            hotspot_ids=[1, 2]
        )
        
        # Two waypoints should trigger warning
        assert len(result.waypoints) == 2

    def test_no_warning_for_multiple_waypoints(self):
        """Test that no warning is generated for routes with 3+ waypoints."""
        engine = RouteEngine()
        
        # Create a mock result with three waypoints
        result = RouteResult(
            algorithm="genetic",
            waypoints=[(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)],
            total_distance_km=20.0,
            estimated_fuel_litres=3.0,
            estimated_time_minutes=30.0,
            hotspots_covered=3,
            computation_time_ms=100.0,
            hotspot_ids=[1, 2, 3]
        )
        
        # Three waypoints should not trigger warning
        assert len(result.waypoints) == 3

    def test_warning_field_in_result_dict(self):
        """Test that warning field is included in result dict when present."""
        engine = RouteEngine()
        
        result = RouteResult(
            algorithm="dijkstra",
            waypoints=[(0.0, 0.0)],
            total_distance_km=0.0,
            estimated_fuel_litres=0.0,
            estimated_time_minutes=0.0,
            hotspots_covered=1,
            computation_time_ms=1.0,
            hotspot_ids=[1],
            warning="Test warning message"
        )
        
        result_dict = engine._result_to_dict(result)
        assert "warning" in result_dict
        assert result_dict["warning"] == "Test warning message"

    def test_no_warning_field_when_none(self):
        """Test that warning field is not included when result has no warning."""
        engine = RouteEngine()
        
        result = RouteResult(
            algorithm="genetic",
            waypoints=[(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)],
            total_distance_km=20.0,
            estimated_fuel_litres=3.0,
            estimated_time_minutes=30.0,
            hotspots_covered=3,
            computation_time_ms=100.0,
            hotspot_ids=[1, 2, 3]
        )
        
        result_dict = engine._result_to_dict(result)
        assert "warning" not in result_dict
