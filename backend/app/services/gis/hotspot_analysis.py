from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Sequence, Tuple

import numpy as np
from geoalchemy2.shape import from_shape, to_shape
from scipy.stats import gaussian_kde
from shapely.geometry import MultiPoint, Point
from sklearn.cluster import DBSCAN

from app import db
from app.models.models import Hotspot, HotspotHistory, Incident


# DBSCAN hyperparameters documented in docs/03_GIS_HOTSPOT_ANALYSIS.md.
DBSCAN_EPSILON = 0.008
DBSCAN_MIN_SAMPLES = 4

# Hotspot matching and lifecycle parameters
MATCH_RADIUS_METERS = 500  # Match radius in meters (true Haversine distance)
COOLING_THRESHOLD = 2  # Consecutive missed runs before dormant (12 hours at 6-hour cadence)
ANALYSIS_CADENCE_HOURS = 6  # Production run cadence


class HotspotAnalysisService:
    """Spatial analysis service for DBSCAN hotspots and KDE heatmap data."""

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def _match_clusters_to_hotspots(self, new_clusters: List[dict]) -> dict:
        """
        Match new DBSCAN clusters to existing hotspots using Haversine distance.
        
        CRITICAL: Includes ALL hotspots in candidate pool, including dormant.
        This ensures dormant hotspots can be reactivated.
        
        Returns: {
            'matched': [(cluster, hotspot, distance)],
            'unmatched_clusters': [cluster],
            'unmatched_hotspots': [hotspot]
        }
        """
        # Query ALL hotspots (no status filter) for matching candidates
        existing_hotspots = db.session.query(Hotspot).all()
        
        if not existing_hotspots:
            return {
                'matched': [],
                'unmatched_clusters': new_clusters,
                'unmatched_hotspots': []
            }
        
        # Calculate all pairwise distances
        candidate_pairs = []
        for cluster in new_clusters:
            cluster_lat = cluster['centroid_lat']
            cluster_lon = cluster['centroid_lon']
            
            for hotspot in existing_hotspots:
                # Extract centroid from PostGIS geometry
                hotspot_geom = to_shape(hotspot.centroid)
                hotspot_lat = hotspot_geom.y
                hotspot_lon = hotspot_geom.x
                
                distance = self._haversine_distance(
                    cluster_lat, cluster_lon, hotspot_lat, hotspot_lon
                )
                
                if distance <= MATCH_RADIUS_METERS:
                    candidate_pairs.append({
                        'cluster': cluster,
                        'hotspot': hotspot,
                        'distance': distance
                    })
        
        # Greedy nearest-neighbor with mutual best match
        candidate_pairs.sort(key=lambda x: x['distance'])
        
        matched = []
        claimed_clusters = set()
        claimed_hotspots = set()
        
        for pair in candidate_pairs:
            cluster_id = id(pair['cluster'])
            hotspot_id = pair['hotspot'].hotspot_id
            
            if cluster_id not in claimed_clusters and hotspot_id not in claimed_hotspots:
                matched.append((pair['cluster'], pair['hotspot'], pair['distance']))
                claimed_clusters.add(cluster_id)
                claimed_hotspots.add(hotspot_id)
        
        unmatched_clusters = [
            c for c in new_clusters 
            if id(c) not in claimed_clusters
        ]
        
        unmatched_hotspots = [
            h for h in existing_hotspots 
            if h.hotspot_id not in claimed_hotspots
        ]
        
        return {
            'matched': matched,
            'unmatched_clusters': unmatched_clusters,
            'unmatched_hotspots': unmatched_hotspots
        }

    def _update_hotspot_status(self, hotspot: Hotspot, is_matched: bool) -> None:
        """Update hotspot status based on match state and lifecycle rules."""
        if is_matched:
            hotspot.consecutive_misses = 0
            hotspot.last_matched_at = self._now()
            
            if hotspot.status == 'emerging':
                hotspot.status = 'active'
            elif hotspot.status in ['cooling', 'dormant']:
                hotspot.status = 'active'  # Reactivation
            # 'active' stays 'active'
        else:
            hotspot.consecutive_misses += 1
            
            if hotspot.status == 'active':
                if hotspot.consecutive_misses == 1:
                    hotspot.status = 'cooling'
                elif hotspot.consecutive_misses > COOLING_THRESHOLD:
                    hotspot.status = 'dormant'
            elif hotspot.status == 'cooling':
                if hotspot.consecutive_misses > COOLING_THRESHOLD:
                    hotspot.status = 'dormant'
            # 'dormant' stays 'dormant'
            # 'emerging' stays 'emerging' (shouldn't happen, but defensive)

    def run_hotspot_analysis(self, days_back: int = 30) -> dict:
        incidents = self._fetch_recent_incidents(days_back)
        coords, located_incidents = self._extract_coordinates(incidents)

        if len(coords) < DBSCAN_MIN_SAMPLES:
            self._update_hotspots_incremental([])
            return {
                "hotspots_generated": 0,
                "source_count": len(located_incidents),
                "noise_points": len(located_incidents),
            }

        labels = DBSCAN(
            eps=DBSCAN_EPSILON,
            min_samples=DBSCAN_MIN_SAMPLES,
        ).fit_predict(coords)

        clusters = []
        for label in sorted(set(labels)):
            if label == -1:
                continue

            cluster_incidents = [
                incident
                for incident, point_label in zip(located_incidents, labels)
                if point_label == label
            ]
            clusters.append(self._build_hotspot(cluster_incidents))

        self._update_hotspots_incremental(clusters)

        return {
            "hotspots_generated": len(clusters),
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
        # Return cluster labels as before for backward compatibility
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

    def _build_hotspot(self, incidents: List[Incident]) -> dict:
        """Build hotspot data from incidents (returns dict, not model)."""
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

        risk_total, volume, severity, recency = self._calculate_risk_score(incidents)
        
        return {
            'centroid_lat': float(centroid.y),
            'centroid_lon': float(centroid.x),
            'convex_hull': boundary,
            'incident_count': len(incidents),
            'risk_score': risk_total,
            'volume_score': volume,
            'severity_score': severity,
            'recency_score': recency,
            'dominant_category': self._dominant_category(incidents),
        }

    def _boundary_from_points(self, points: List[Point]):
        if not points:
            # Return a default small polygon around Harare city center
            from shapely.geometry import Polygon
            return Polygon([
                (31.0522 - 0.001, -17.8292 - 0.001),
                (31.0522 + 0.001, -17.8292 - 0.001),
                (31.0522 + 0.001, -17.8292 + 0.001),
                (31.0522 - 0.001, -17.8292 + 0.001)
            ])
        multipoint = MultiPoint(points)
        hull = multipoint.convex_hull
        if hull.geom_type == "Polygon":
            return hull.buffer(0.001)
        return hull.buffer(0.001)

    def _update_hotspots_incremental(self, new_clusters: List[dict]) -> None:
        """Update hotspots incrementally with matching and status lifecycle."""
        run_timestamp = self._now()
        
        # Match new clusters to existing hotspots
        matching_result = self._match_clusters_to_hotspots(new_clusters)
        
        # Process matched pairs
        for cluster, hotspot, distance in matching_result['matched']:
            hotspot.centroid = from_shape(
                Point(cluster['centroid_lon'], cluster['centroid_lat']),
                srid=4326
            )
            hotspot.convex_hull = from_shape(cluster['convex_hull'], srid=4326)
            hotspot.incident_count = cluster['incident_count']
            hotspot.risk_score = cluster['risk_score']
            hotspot.dominant_category = cluster['dominant_category']
            hotspot.updated_at = run_timestamp
            self._update_hotspot_status(hotspot, is_matched=True)
        
        # Create new hotspots for unmatched clusters
        for cluster in matching_result['unmatched_clusters']:
            new_hotspot = Hotspot(
                centroid=from_shape(
                    Point(cluster['centroid_lon'], cluster['centroid_lat']),
                    srid=4326
                ),
                convex_hull=from_shape(cluster['convex_hull'], srid=4326),
                incident_count=cluster['incident_count'],
                risk_score=cluster['risk_score'],
                dominant_category=cluster['dominant_category'],
                status='emerging',
                consecutive_misses=0,
                first_detected_at=run_timestamp,
                last_matched_at=run_timestamp,
                updated_at=run_timestamp
            )
            db.session.add(new_hotspot)
        
        # Update unmatched existing hotspots
        for hotspot in matching_result['unmatched_hotspots']:
            self._update_hotspot_status(hotspot, is_matched=False)
            hotspot.updated_at = run_timestamp
        
        db.session.commit()
        
        # Log history for all hotspots
        self._log_hotspot_history(run_timestamp)

    def _log_hotspot_history(self, run_timestamp: datetime) -> None:
        """Log history entry for all hotspots after each run."""
        all_hotspots = db.session.query(Hotspot).all()
        
        for hotspot in all_hotspots:
            # Recalculate component scores for history logging
            # Get recent incidents for this hotspot
            from sqlalchemy import func
            from sqlalchemy.types import Float
            
            # Get incidents within match radius of hotspot centroid
            hotspot_geom = to_shape(hotspot.centroid)
            hotspot_lat = hotspot_geom.y
            hotspot_lon = hotspot_geom.x
            
            # Simple distance filter for incidents (not using PostGIS ST_Distance for compatibility)
            recent_incidents = self._fetch_recent_incidents(30)
            nearby_incidents = []
            for incident in recent_incidents:
                if incident.lat is None or incident.lng is None:
                    continue
                try:
                    incident_lat = float(incident.lat)
                    incident_lon = float(incident.lng)
                    distance = self._haversine_distance(
                        hotspot_lat, hotspot_lon, incident_lat, incident_lon
                    )
                    if distance <= MATCH_RADIUS_METERS:
                        nearby_incidents.append(incident)
                except Exception:
                    continue
            
            # Calculate component scores
            risk_total, volume, severity, recency = self._calculate_risk_score(nearby_incidents)
            
            history_entry = HotspotHistory(
                hotspot_id=hotspot.hotspot_id,
                run_timestamp=run_timestamp,
                centroid=hotspot.centroid,
                incident_count=hotspot.incident_count,
                risk_score=hotspot.risk_score,
                volume_score=volume,
                severity_score=severity,
                recency_score=recency,
                status=hotspot.status,
                dominant_category=hotspot.dominant_category
            )
            db.session.add(history_entry)
        
        db.session.commit()

    def _calculate_risk_score(self, incidents: List[Incident]) -> tuple[float, float, float, float]:
        """
        Composite risk score: 0.0 to 1.0.

        Returns: (total_score, volume_score, severity_score, recency_score)
        RiskScore = 0.4 * Volume + 0.4 * Severity + 0.2 * Recency
        """
        if not incidents:
            return 0.0, 0.0, 0.0, 0.0

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

        total_score = round(
            (0.4 * volume_score) + (0.4 * severity_score) + (0.2 * recency_score),
            3,
        )
        
        return total_score, volume_score, severity_score, recency_score

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
