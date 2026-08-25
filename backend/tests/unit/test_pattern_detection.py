"""
Unit tests for pattern detection service.
"""
import pytest
from datetime import datetime, timedelta
from app.services.pattern_detection.similarity_engine import SimilarityEngine
from app.services.pattern_detection.pattern_recognizer import PatternRecognizer
from app.models.models import Incident, User
from app import db


class TestSimilarityEngine:
    
    def test_text_similarity_calculation(self):
        """Test that text similarity calculation works with similar texts."""
        engine = SimilarityEngine()
        sim = engine._text_similarity(
            "Armed robbery at gunpoint",
            "Robbery with a firearm"
        )
        assert sim > 0.2  # Should have some similarity (adjusted for Jaccard)
    
    def test_text_similarity_identical(self):
        """Test that identical texts have high similarity."""
        engine = SimilarityEngine()
        sim = engine._text_similarity(
            "Armed robbery at gunpoint",
            "Armed robbery at gunpoint"
        )
        assert sim == 1.0  # Should be identical
    
    def test_text_similarity_different(self):
        """Test that completely different texts have low similarity."""
        engine = SimilarityEngine()
        sim = engine._text_similarity(
            "Armed robbery at gunpoint",
            "Traffic violation on main street"
        )
        assert sim < 0.5  # Should have low similarity
    
    def test_spatial_similarity_same_location(self):
        """Test that same location has high similarity."""
        engine = SimilarityEngine()
        sim = engine._spatial_similarity(
            (-17.8292, 31.0522),  # CBD
            (-17.8292, 31.0522)   # Same point
        )
        assert sim == 1.0  # Same location should be 1.0
    
    def test_spatial_similarity_close_location(self):
        """Test that close locations have high similarity."""
        engine = SimilarityEngine()
        sim = engine._spatial_similarity(
            (-17.8292, 31.0522),  # CBD
            (-17.8302, 31.0532)   # ~150m away
        )
        assert sim > 0.8  # Should be highly similar
    
    def test_spatial_similarity_far_location(self):
        """Test that far locations have low similarity."""
        engine = SimilarityEngine()
        sim = engine._spatial_similarity(
            (-17.8292, 31.0522),  # CBD
            (-18.0000, 31.0000)   # ~20km away
        )
        assert sim < 0.2  # Should have low similarity
    
    def test_temporal_similarity_recent(self):
        """Test that recent times have high similarity."""
        engine = SimilarityEngine()
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        sim = engine._temporal_similarity(now, one_hour_ago)
        assert sim > 0.8  # Should be highly similar
    
    def test_temporal_similarity_old(self):
        """Test that old times have low similarity."""
        engine = SimilarityEngine()
        now = datetime.utcnow()
        two_days_ago = now - timedelta(days=2)
        sim = engine._temporal_similarity(now, two_days_ago)
        assert sim < 0.2  # Should have low similarity
    
    def test_category_similarity_exact_match(self):
        """Test that exact category match returns 1.0."""
        engine = SimilarityEngine()
        sim = engine._category_similarity("robbery", "robbery")
        assert sim == 1.0
    
    def test_category_similarity_semantic_match(self):
        """Test that semantically related categories have high similarity."""
        engine = SimilarityEngine()
        sim = engine._category_similarity("robbery", "theft")
        assert sim == 0.8  # Should be semantically similar (theft is in robbery's group)
    
    def test_category_similarity_no_match(self):
        """Test that unrelated categories have low similarity."""
        engine = SimilarityEngine()
        sim = engine._category_similarity("robbery", "noise_complaint")
        assert sim == 0.0  # Should not be similar
    
    def test_haversine_distance_calculation(self):
        """Test Haversine distance calculation."""
        engine = SimilarityEngine()
        # Distance between two points in Harare (approximately 1km apart)
        distance = engine._haversine_distance(
            -17.8292, 31.0522,
            -17.8383, 31.0530
        )
        assert 0.8 < distance < 1.2  # Should be approximately 1km


class TestPatternRecognizer:
    
    def test_detect_serial_crimes_requires_minimum_incidents(self):
        """Test that serial crime detection requires minimum incidents."""
        recognizer = PatternRecognizer()
        # Should return empty for < 3 incidents
        assert len(recognizer.detect_serial_crimes([])) == 0
    
    def test_detect_crime_sprees_requires_minimum_incidents(self):
        """Test that crime spree detection requires minimum incidents."""
        recognizer = PatternRecognizer()
        # Should return empty for < 3 incidents
        assert len(recognizer.detect_crime_sprees([])) == 0
    
    def test_detect_repeat_locations_requires_minimum_incidents(self):
        """Test that repeat location detection requires minimum incidents."""
        recognizer = PatternRecognizer()
        # Should return empty for < 2 incidents
        assert len(recognizer.detect_repeat_locations([])) == 0
    
    def test_detect_geographic_patterns_with_no_incidents(self):
        """Test geographic pattern detection with no incidents."""
        recognizer = PatternRecognizer()
        patterns = recognizer.detect_geographic_patterns([])
        assert len(patterns) == 0
    
    def test_get_dominant_category(self):
        """Test dominant category calculation."""
        recognizer = PatternRecognizer()
        # Create mock incidents
        class MockIncident:
            def __init__(self, category):
                self.category = category
        
        incidents = [
            MockIncident("robbery"),
            MockIncident("robbery"),
            MockIncident("theft")
        ]
        dominant = recognizer._get_dominant_category(incidents)
        assert dominant == "robbery"
    
    def test_calculate_time_span(self):
        """Test time span calculation."""
        recognizer = PatternRecognizer()
        # Create mock incidents
        class MockIncident:
            def __init__(self, created_at):
                self.created_at = created_at
        
        now = datetime.utcnow()
        incidents = [
            MockIncident(now - timedelta(days=2)),
            MockIncident(now)
        ]
        time_span = recognizer._calculate_time_span(incidents)
        assert 1.9 < time_span < 2.1  # Should be approximately 2 days
    
    def test_normalize_time(self):
        """Test time normalization."""
        recognizer = PatternRecognizer()
        # Test at noon
        noon = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
        normalized = recognizer._normalize_time(noon)
        assert 0.49 < normalized < 0.51  # Should be approximately 0.5 (noon)


class TestPatternDetectionIntegration:
    """Integration tests for pattern detection with database."""
    
    @pytest.fixture
    def sample_incidents(self, db_session):
        """Create sample incidents for testing."""
        # Create a test user
        user = User(
            email="test@example.com",
            password_hash="test_hash",
            role="community"
        )
        db_session.add(user)
        db_session.flush()
        
        # Create similar incidents (potential serial crime)
        base_time = datetime.utcnow()
        incidents = []
        for i in range(3):
            incident = Incident(
                raw_text=f"Armed robbery at gunpoint in city center {i}",
                category="robbery",
                severity="HIGH",
                status="TRIAGED",
                lat=-17.8292 + (i * 0.001),  # Slightly different locations
                lng=31.0522 + (i * 0.001),
                reported_by_id=user.id,
                created_at=base_time - timedelta(hours=i)
            )
            incidents.append(incident)
            db_session.add(incident)
        
        db_session.commit()
        return incidents
    
    def test_pattern_detection_with_sample_data(self, db_session, sample_incidents):
        """Test pattern detection with sample data."""
        recognizer = PatternRecognizer()
        patterns = recognizer.detect_all_patterns(days_back=7)
        
        # Should detect some patterns
        assert isinstance(patterns, dict)
        assert 'serial_crimes' in patterns
        assert 'crime_sprees' in patterns
        assert 'repeat_locations' in patterns
        assert 'geographic_patterns' in patterns
    
    def test_similarity_engine_with_real_incidents(self, db_session, sample_incidents):
        """Test similarity engine with real incident objects."""
        engine = SimilarityEngine()
        incident1 = sample_incidents[0]
        incident2 = sample_incidents[1]
        
        similarity = engine.calculate_comprehensive_similarity(incident1, incident2)
        
        # Should have a composite score
        assert 'composite_score' in similarity
        assert 'text_similarity' in similarity
        assert 'spatial_similarity' in similarity
        assert 'temporal_similarity' in similarity
        assert 'category_similarity' in similarity
        
        # Composite score should be reasonable
        assert 0.0 <= similarity['composite_score'] <= 1.0
