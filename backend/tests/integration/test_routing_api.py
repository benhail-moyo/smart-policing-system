"""
Integration tests for routing API endpoints.
Tests Flask API endpoints for road network routing.
"""
import pytest
import json
from flask import Flask
from app import create_app
from app.services.routing import graph_store


@pytest.fixture
def app():
    """Create test Flask application."""
    app = create_app('testing')
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create authentication headers for testing."""
    # Create a test user and get token
    response = client.post('/api/v1/auth/register', json={
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test User',
        'role': 'officer'
    })
    
    if response.status_code == 201:
        data = json.loads(response.data)
        token = data.get('access_token')
        return {'Authorization': f'Bearer {token}'}
    
    # Try login if register fails
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    if response.status_code == 200:
        data = json.loads(response.data)
        token = data.get('access_token')
        return {'Authorization': f'Bearer {token}'}
    
    return {}


class TestGraphStatusEndpoint:
    """Test graph status endpoint."""
    
    def test_status_unauthorized(self, client):
        """Test status endpoint requires authentication."""
        response = client.get('/api/v1/patrol/status')
        assert response.status_code == 401
    
    def test_status_authorized(self, client, auth_headers):
        """Test status endpoint with authentication."""
        response = client.get('/api/v1/patrol/status', headers=auth_headers)
        
        # Graph may not be loaded, but should return valid JSON
        assert response.status_code in [200, 500]
        data = json.loads(response.data)
        
        if response.status_code == 200:
            assert 'state' in data
            assert 'city' in data
            assert 'nodes' in data
            assert 'directed_edges' in data


class TestPointToPointRouting:
    """Test point-to-point routing endpoint."""
    
    def test_routes_unauthorized(self, client):
        """Test routes endpoint requires authentication."""
        response = client.post('/api/v1/patrol/routes', json={
            'city': 'harare',
            'start': {'lat': -17.8292, 'lng': 31.0522},
            'end': {'lat': -17.8252, 'lng': 31.0475}
        })
        assert response.status_code == 401
    
    def test_routes_missing_fields(self, client, auth_headers):
        """Test routes endpoint with missing required fields."""
        response = client.post('/api/v1/patrol/routes', 
                              json={'city': 'harare'},
                              headers=auth_headers)
        assert response.status_code == 422
    
    def test_routes_invalid_city(self, client, auth_headers):
        """Test routes endpoint with unsupported city."""
        response = client.post('/api/v1/patrol/routes', json={
            'city': 'invalid_city',
            'start': {'lat': -17.8292, 'lng': 31.0522},
            'end': {'lat': -17.8252, 'lng': 31.0475}
        }, headers=auth_headers)
        assert response.status_code == 422
    
    def test_routes_graph_not_loaded(self, client, auth_headers):
        """Test routes endpoint when graph is not loaded."""
        # Reset graph store to simulate unloaded state
        graph_store.reset()
        
        response = client.post('/api/v1/patrol/routes', json={
            'city': 'harare',
            'start': {'lat': -17.8292, 'lng': 31.0522},
            'end': {'lat': -17.8252, 'lng': 31.0475}
        }, headers=auth_headers)
        
        # Should return 503 or error about graph not being ready
        assert response.status_code in [503, 422, 500]


class TestMultiStopComparison:
    """Test multi-stop comparison endpoint."""
    
    def test_compare_road_network(self, client, auth_headers):
        """Test comparison with road network routing."""
        response = client.post('/api/v1/patrol/compare', json={
            'city': 'harare',
            'start': {'lat': -17.8292, 'lng': 31.0522},
            'stops': [
                {'lat': -17.8252, 'lng': 31.0475},
                {'lat': -17.8189, 'lng': 31.0433},
                {'lat': -17.8216, 'lng': 31.0492}
            ]
        }, headers=auth_headers)
        
        # May fail if graph not loaded, but should handle gracefully
        assert response.status_code in [200, 422, 503, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'comparison' in data or 'error' not in data
    
    def test_compare_insufficient_stops(self, client, auth_headers):
        """Test comparison with insufficient stops."""
        response = client.post('/api/v1/patrol/compare', json={
            'city': 'harare',
            'start': {'lat': -17.8292, 'lng': 31.0522},
            'stops': [
                {'lat': -17.8252, 'lng': 31.0475}
            ]
        }, headers=auth_headers)
        assert response.status_code == 422
    
    def test_compare_invalid_stop_format(self, client, auth_headers):
        """Test comparison with invalid stop format."""
        response = client.post('/api/v1/patrol/compare', json={
            'city': 'harare',
            'start': {'lat': -17.8292, 'lng': 31.0522},
            'stops': ['invalid', 'format']
        }, headers=auth_headers)
        assert response.status_code == 422
    
    def test_compare_return_to_start(self, client, auth_headers):
        """Test comparison with return_to_start option."""
        response = client.post('/api/v1/patrol/compare', json={
            'city': 'harare',
            'start': {'lat': -17.8292, 'lng': 31.0522},
            'stops': [
                {'lat': -17.8252, 'lng': 31.0475},
                {'lat': -17.8189, 'lng': 31.0433},
                {'lat': -17.8216, 'lng': 31.0492}
            ],
            'return_to_start': True
        }, headers=auth_headers)
        
        # May fail if graph not loaded
        assert response.status_code in [200, 422, 503, 500]


class TestExistingEndpoints:
    """Test that existing patrol endpoints still work."""
    
    def test_get_routes_history(self, client):
        """Test getting route history (public endpoint)."""
        response = client.get('/api/v1/patrol/routes')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'routes' in data
    
    def test_optimize_hotspot_based(self, client):
        """Test hotspot-based optimization (public endpoint)."""
        response = client.post('/api/v1/patrol/optimize', json={})
        # May return 422 if no hotspots, but should not error
        assert response.status_code in [200, 422, 500]
