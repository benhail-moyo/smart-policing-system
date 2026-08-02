from app import create_app, db
from app.services.gis.hotspot_analysis import hotspot_service


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
