from app import create_app, db
from app.services.gis.hotspot_analysis import hotspot_service
from app.models.models import Hotspot
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from datetime import datetime, timezone
import uuid


def test_generate_kde_heatmap_returns_serializable_payload():
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        result = hotspot_service.generate_kde_heatmap(
            bbox=(30.95, -18.05, 31.20, -17.70),
            resolution=20,
            days_back=30,
        )

        assert isinstance(result, dict)
        assert "heat_points" in result
        assert "count" in result
        assert isinstance(result["heat_points"], list)
        assert isinstance(result["count"], int)


def test_haversine_distance_accuracy():
    """Test that Haversine uses meters, not degree approximation."""
    app = create_app("testing")
    with app.app_context():
        # Two points with same degree-delta at different latitudes
        # At equator: 0.005 degrees ≈ 555m
        # At Harare latitude: 0.005 degrees ≈ 530m
        # If using degree approximation, both would match 500m threshold identically
        # If using Haversine, they should differ
        
        # Near equator
        dist_equator = hotspot_service._haversine_distance(0.0, 0.0, 0.005, 0.005)
        
        # Near Harare latitude
        dist_harare = hotspot_service._haversine_distance(-17.83, 31.05, -17.825, 31.055)
        
        # These should NOT be equal (degree approximation would make them equal)
        assert abs(dist_equator - dist_harare) > 20  # At least 20m difference
        
        # Both should be approximately correct distances
        assert 500 < dist_equator < 600  # ~555m at equator
        assert 500 < dist_harare < 600  # ~530m at Harare


def test_dormant_hotspot_reactivation():
    """Test that dormant hotspots are included in matching and can be reactivated."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        
        # Create a dormant hotspot
        dormant_hotspot = Hotspot(
            hotspot_id=uuid.uuid4(),
            centroid=from_shape(Point(31.05, -17.83), srid=4326),
            status='dormant',
            consecutive_misses=3,
            incident_count=5,
            risk_score=0.7,
            dominant_category="Theft",
            first_detected_at=datetime.now(timezone.utc),
            last_matched_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(dormant_hotspot)
        db.session.commit()
        
        # Create new cluster near dormant hotspot (within 500m)
        new_cluster = {
            'centroid_lat': -17.830,
            'centroid_lon': 31.051,
            'convex_hull': Point(31.051, -17.830).buffer(0.001),
            'incident_count': 3,
            'risk_score': 0.6,
            'dominant_category': "Theft"
        }
        
        # Run matching
        result = hotspot_service._match_clusters_to_hotspots([new_cluster])
        
        # Assert reactivation, not new hotspot creation
        assert len(result['matched']) == 1
        assert result['matched'][0][1].hotspot_id == dormant_hotspot.hotspot_id
        assert len(result['unmatched_clusters']) == 0
        assert len(result['unmatched_hotspots']) == 0


def test_status_lifecycle_transitions():
    """Test complete status lifecycle: emerging→active→cooling→dormant→active."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        
        # Create emerging hotspot
        hotspot = Hotspot(
            hotspot_id=uuid.uuid4(),
            centroid=from_shape(Point(31.05, -17.83), srid=4326),
            status='emerging',
            consecutive_misses=0,
            incident_count=5,
            risk_score=0.7,
            dominant_category="Theft",
            first_detected_at=datetime.now(timezone.utc),
            last_matched_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(hotspot)
        db.session.commit()
        
        # Test emerging → active on match
        hotspot_service._update_hotspot_status(hotspot, is_matched=True)
        assert hotspot.status == 'active'
        assert hotspot.consecutive_misses == 0
        
        # Test active → cooling on first miss
        hotspot_service._update_hotspot_status(hotspot, is_matched=False)
        assert hotspot.status == 'cooling'
        assert hotspot.consecutive_misses == 1
        
        # Test cooling → dormant after threshold
        hotspot_service._update_hotspot_status(hotspot, is_matched=False)
        hotspot_service._update_hotspot_status(hotspot, is_matched=False)
        assert hotspot.status == 'dormant'
        assert hotspot.consecutive_misses == 3
        
        # Test dormant → active on reactivation
        hotspot_service._update_hotspot_status(hotspot, is_matched=True)
        assert hotspot.status == 'active'
        assert hotspot.consecutive_misses == 0


def test_no_hotspot_deletion_regression():
    """Replay historical runs and verify no hotspot is ever deleted."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        
        # Create initial hotspots
        hotspot1_id = uuid.uuid4()
        hotspot2_id = uuid.uuid4()
        
        hotspot1 = Hotspot(
            hotspot_id=hotspot1_id,
            centroid=from_shape(Point(31.05, -17.83), srid=4326),
            status='active',
            consecutive_misses=0,
            incident_count=5,
            risk_score=0.7,
            dominant_category="Theft",
            first_detected_at=datetime.now(timezone.utc),
            last_matched_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        hotspot2 = Hotspot(
            hotspot_id=hotspot2_id,
            centroid=from_shape(Point(31.06, -17.84), srid=4326),
            status='active',
            consecutive_misses=0,
            incident_count=3,
            risk_score=0.5,
            dominant_category="Assault",
            first_detected_at=datetime.now(timezone.utc),
            last_matched_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.session.add(hotspot1)
        db.session.add(hotspot2)
        db.session.commit()
        
        initial_hotspot_ids = {hotspot1_id, hotspot2_id}
        
        # Simulate multiple analysis runs
        for run in range(5):
            # In some runs, match only one hotspot
            if run % 2 == 0:
                new_clusters = [{
                    'centroid_lat': -17.83,
                    'centroid_lon': 31.05,
                    'convex_hull': Point(31.05, -17.83).buffer(0.001),
                    'incident_count': 4,
                    'risk_score': 0.6,
                    'dominant_category': "Theft"
                }]
            else:
                new_clusters = [{
                    'centroid_lat': -17.84,
                    'centroid_lon': 31.06,
                    'convex_hull': Point(31.06, -17.84).buffer(0.001),
                    'incident_count': 2,
                    'risk_score': 0.4,
                    'dominant_category': "Assault"
                }]
            
            hotspot_service._update_hotspots_incremental(new_clusters)
            
            # Verify original hotspots still exist (may be dormant)
            current_hotspots = db.session.query(Hotspot).all()
            current_ids = {h.hotspot_id for h in current_hotspots}
            
            # Original hotspots should still be in the system
            assert initial_hotspot_ids.issubset(current_ids), f"Run {run}: Original hotspots deleted"
        
        # Final verification: all original hotspots still exist
        final_hotspots = db.session.query(Hotspot).all()
        final_ids = {h.hotspot_id for h in final_hotspots}
        assert initial_hotspot_ids.issubset(final_ids), "Original hotspots were deleted"
