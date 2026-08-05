import json
import pytest
from app import create_app, db
from app.models.models import User, Incident, Hotspot, PatrolRoute


@pytest.fixture
def app_instance():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_auth_register_and_login(client):
    # Register user
    res = client.post("/api/v1/auth/register", json={
        "name": "Test Officer",
        "email": "officer_test@policing.gov.zw",
        "password": "securepassword123",
        "role": "officer"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "token" in data
    assert data["user"]["email"] == "officer_test@policing.gov.zw"

    # Login user
    login_res = client.post("/api/v1/auth/login", json={
        "email": "officer_test@policing.gov.zw",
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    login_data = login_res.get_json()
    assert "token" in login_data
    token = login_data["token"]

    # Access /me endpoint
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.get_json()["user"]["email"] == "officer_test@policing.gov.zw"


def test_incident_creation_and_stats(client):
    # Submit report
    res = client.post("/api/v1/incidents/", json={
        "type": "Armed Robbery",
        "description": "Suspicious armed robbery reported near CBD commercial bank",
        "severity": 5,
        "suburb": "CBD",
        "lat": -17.8292,
        "lng": 31.0522
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "incident" in data
    assert "triage" in data
    assert data["triage"]["priority"] in ("critical", "high")

    # List incidents
    list_res = client.get("/api/v1/incidents/")
    assert list_res.status_code == 200
    incidents = list_res.get_json()["incidents"]
    assert len(incidents) >= 1

    # Get stats
    stats_res = client.get("/api/v1/incidents/stats")
    assert stats_res.status_code == 200
    stats = stats_res.get_json()
    assert "total" in stats
    assert "openCases" in stats
    assert "byPriority" in stats


def test_hotspot_analysis(client):
    analyze_res = client.post("/api/v1/hotspots/analyze", json={"days_back": 30})
    assert analyze_res.status_code == 200
    data = analyze_res.get_json()
    assert "hotspots" in data

    list_res = client.get("/api/v1/hotspots/")
    assert list_res.status_code == 200


def test_patrol_optimization_and_comparison(client):
    cmp_res = client.post("/api/v1/patrol/compare", json={})
    assert cmp_res.status_code == 200
    data = cmp_res.get_json()
    assert "comparison" in data
    assert "recommendedRouteId" in data

    routes_res = client.get("/api/v1/patrol/routes")
    assert routes_res.status_code == 200
    assert "routes" in routes_res.get_json()


def test_ai_crime_analysis_report(client):
    rep_res = client.post("/api/v1/analysis/report", json={"periodDays": 30})
    assert rep_res.status_code == 200
    data = rep_res.get_json()
    assert "report" in data
    assert "narrative" in data["report"]
    assert "summary" in data["report"]
    assert "recommendations" in data["report"]


def test_seed_database(client):
    seed_res = client.post("/api/v1/seed", json={})
    assert seed_res.status_code == 200
    data = seed_res.get_json()
    assert "message" in data
