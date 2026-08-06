from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Sequence, Tuple

import numpy as np
from geoalchemy2.shape import from_shape, to_shape
from scipy.stats import gaussian_kde
from shapely.geometry import MultiPoint, Point
from sklearn.cluster import DBSCAN

from app import db
from app.models.models import Hotspot, Incident


# DBSCAN hyperparameters documented in docs/03_GIS_HOTSPOT_ANALYSIS.md.
DBSCAN_EPSILON = 0.008
DBSCAN_MIN_SAMPLES = 4


class HotspotAnalysisService:
    """Spatial analysis service for DBSCAN hotspots and KDE heatmap data."""

    def run_hotspot_analysis(self, days_back: int = 30) -> dict:
        incidents = self._fetch_recent_incidents(days_back)
        coords, located_incidents = self._extract_coordinates(incidents)

        if len(coords) < DBSCAN_MIN_SAMPLES:
            self._replace_hotspots([])
            return {
                "hotspots_generated": 0,
                "source_count": len(located_incidents),
                "noise_points": len(located_incidents),
            }

        labels = DBSCAN(
            eps=DBSCAN_EPSILON,
            min_samples=DBSCAN_MIN_SAMPLES,
        ).fit_predict(coords)

        hotspots = []
        for label in sorted(set(labels)):
            if label == -1:
                continue

            cluster_incidents = [
                incident
                for incident, point_label in zip(located_incidents, labels)
                if point_label == label
            ]
            hotspots.append(self._build_hotspot(cluster_incidents))

        self._replace_hotspots(hotspots)

        return {
            "hotspots_generated": len(hotspots),
            "source_count": len(located_incidents),
            "noise_points": int(list(labels).count(-1)),
        }

    def tune_dbscan_parameters(self, days_back: int = 30) -> dict:
        """
        Tests epsilon values for dissertation parameter sensitivity analysis.

        Returns a JSON-friendly mapping of epsilon to cluster/noise counts.
        """
        incidents = self._fetch_recent_incidents(days_back)
        coords, _ = self._extract_coordinates(incidents)

        if len(coords) < DBSCAN_MIN_SAMPLES:
            return {
                str(eps): {"clusters": 0, "noise_points": len(coords)}
                for eps in [0.003, 0.005, 0.008, 0.010, 0.015, 0.020]
            }

        results = {}
        for eps in [0.003, 0.005, 0.008, 0.010, 0.015, 0.020]:
            labels = DBSCAN(eps=eps, min_samples=DBSCAN_MIN_SAMPLES).fit_predict(coords)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = int(list(labels).count(-1))
            results[str(eps)] = {"clusters": n_clusters, "noise_points": n_noise}

        return results

    def generate_kde_heatmap(
        self,
        bbox: Tuple[float, float, float, float],
        resolution: int = 50,
        days_back: int = 90,
    ) -> dict:
        """
        Generate Leaflet.heat-compatible points for incidents inside a bbox.

        bbox order is (min_lng, min_lat, max_lng, max_lat).
        """
        min_lng, min_lat, max_lng, max_lat = bbox
        resolution = max(10, min(int(resolution), 150))

        incidents = self._fetch_recent_incidents(days_back)
        coords, _ = self._extract_coordinates(incidents)
        if len(coords) < 2:
            return {"heat_points": [], "count": 0}

        points = [
            (float(lat), float(lng))
            for lat, lng in coords
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng
        ]
        if len(points) < 2:
            return {"heat_points": [], "count": 0}

        lat_values = np.array([p[0] for p in points], dtype=float)
        lng_values = np.array([p[1] for p in points], dtype=float)

        lat_grid = np.linspace(min_lat, max_lat, resolution)
        lng_grid = np.linspace(min_lng, max_lng, resolution)
        lng_mesh, lat_mesh = np.meshgrid(lng_grid, lat_grid)

        try:
            kde = gaussian_kde(np.vstack([lat_values, lng_values]))
            intensities = kde(np.vstack([lat_mesh.ravel(), lng_mesh.ravel()]))
        except np.linalg.LinAlgError:
            return {"heat_points": [], "count": 0}

        intensities = intensities.reshape(lat_mesh.shape)
        threshold = float(intensities.max()) * 0.001 if intensities.size else 0.0

        heat_points = []
        for i, lat in enumerate(lat_grid):
            for j, lng in enumerate(lng_grid):
                intensity = float(intensities[i][j])
                if intensity > threshold:
                    heat_points.append([float(lat), float(lng), intensity])

        if heat_points:
            max_intensity = max(point[2] for point in heat_points)
            heat_points = [
                [point[0], point[1], round(point[2] / max_intensity, 6)]
                for point in heat_points
            ]

        return {"heat_points": heat_points, "count": len(heat_points)}

    # Backward-compatible wrappers for earlier scaffold callers.
    def analyze(self, incidents: Sequence[Incident] | None = None):
        if incidents is None:
            return self.run_hotspot_analysis()
        coords, located_incidents = self._extract_coordinates(incidents)
        if len(coords) < DBSCAN_MIN_SAMPLES:
            return {"clusters": [], "source_count": len(located_incidents)}
        labels = DBSCAN(eps=DBSCAN_EPSILON, min_samples=DBSCAN_MIN_SAMPLES).fit_predict(coords)
        return {"clusters": sorted(label for label in set(labels) if label != -1), "source_count": len(located_incidents)}

    def heatmap(self, incidents: Sequence[Incident] | None = None):
        if incidents is None:
            return self.generate_kde_heatmap((30.95, -18.05, 31.20, -17.70))
        coords, _ = self._extract_coordinates(incidents)
        return {"points": coords.tolist() if len(coords) else [], "source_count": len(incidents)}

    def _fetch_recent_incidents(self, days_back: int) -> List[Incident]:
        cutoff = self._now() - timedelta(days=max(int(days_back), 1))
        return (
            db.session.query(Incident)
            .filter(Incident.lat.isnot(None))
            .filter(Incident.lng.isnot(None))
            .filter(Incident.created_at >= cutoff)
            .order_by(Incident.created_at.desc())
            .all()
        )

    def _extract_coordinates(self, incidents: Iterable[Incident]):
        coords = []
        located_incidents = []
        for incident in incidents:
            if incident.lat is None or incident.lng is None:
                continue
            try:
                lat = float(incident.lat)
                lng = float(incident.lng)
            except Exception:
                continue
            coords.append([lat, lng])
            located_incidents.append(incident)

        return np.array(coords, dtype=float), located_incidents

    def _build_hotspot(self, incidents: List[Incident]) -> Hotspot:
        # Build a simplified hotspot record using centroid lat/lng and risk metrics
        points = []
        for incident in incidents:
            try:
                lat = float(incident.lat)
                lng = float(incident.lng)
            except Exception:
                continue
            points.append(Point(lng, lat))

        boundary = self._boundary_from_points(points) if points else None
        centroid = boundary.centroid if boundary is not None else Point(-17.8292, 31.0522)

        return Hotspot(
            lat=float(centroid.y),
            lng=float(centroid.x),
            incident_count=len(incidents),
            risk_score=self._calculate_risk_score(incidents),
            dominant_category=self._dominant_category(incidents),
            analysis_date=self._now(),
        )

    def _boundary_from_points(self, points: List[Point]):
        multipoint = MultiPoint(points)
        hull = multipoint.convex_hull
        if hull.geom_type == "Polygon":
            return hull.buffer(0.001)
        return hull.buffer(0.001)

    def _replace_hotspots(self, hotspots: List[Hotspot]) -> None:
        db.session.query(Hotspot).delete()
        for hotspot in hotspots:
            db.session.add(hotspot)
        db.session.commit()

    def _calculate_risk_score(self, incidents: List[Incident]) -> float:
        """
        Composite risk score: 0.0 to 1.0.

        RiskScore = 0.4 * Volume + 0.4 * Severity + 0.2 * Recency
        """
        if not incidents:
            return 0.0

        now = self._now()
        volume_score = min(1.0, len(incidents) / 20.0)

        severity_weights = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.1}
        severity_scores = [
            severity_weights.get(str(incident.severity or "LOW").upper(), 0.1)
            for incident in incidents
        ]
        severity_score = sum(severity_scores) / len(severity_scores)

        recent_cutoff = now - timedelta(days=7)
        recent_count = sum(
            1
            for incident in incidents
            if self._as_aware_datetime(incident.created_at) >= recent_cutoff
        )
        recency_score = min(1.0, recent_count / 5.0)

        return round(
            (0.4 * volume_score) + (0.4 * severity_score) + (0.2 * recency_score),
            3,
        )

    def _dominant_category(self, incidents: List[Incident]) -> str | None:
        categories = [incident.category for incident in incidents if incident.category]
        if not categories:
            return None
        return Counter(categories).most_common(1)[0][0]

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _as_aware_datetime(self, value: datetime | None) -> datetime:
        if value is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


hotspot_service = HotspotAnalysisService()
hotspot_analysis_service = hotspot_service
