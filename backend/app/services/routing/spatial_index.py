"""
Spatial index for efficient nearest-node lookup with accurate distance metrics.
Uses projected coordinates (UTM) with cKDTree for meter-accurate distance queries.
"""
import logging
import numpy as np
from scipy.spatial import cKDTree
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SnapResult:
    """Result of snapping a point to the nearest graph node."""
    node_id: int
    snap_distance_m: float
    node_lat: float
    node_lng: float


class SpatialIndex:
    """
    Spatial index for snapping coordinates to graph nodes.
    Uses projected local CRS with cKDTree for accurate distance queries.
    """
    
    def __init__(self, nodes: Dict[int, Dict[str, float]]):
        """
        Build spatial index from graph nodes.
        
        Args:
            nodes: Dict mapping node_id -> {lat, lng}
        """
        self.nodes = nodes
        self.node_ids = list(nodes.keys())
        
        if not self.node_ids:
            logger.warning("No nodes provided to spatial index")
            self.kdtree = None
            self.projected_coords = None
            self.crs_info = None
            return
        
        # Extract coordinates
        lats = np.array([nodes[nid]['lat'] for nid in self.node_ids])
        lngs = np.array([nodes[nid]['lng'] for nid in self.node_ids])
        
        # Determine appropriate UTM zone for Harare (approx. 31°E)
        # Harare is in UTM zone 36S
        utm_zone = self._get_utm_zone(lats[0], lngs[0])
        self.crs_info = {'utm_zone': utm_zone, 'hemisphere': 'S'}
        
        # Project to UTM for accurate distance calculations
        projected_coords = self._project_to_utm(lats, lngs, utm_zone)
        self.projected_coords = projected_coords
        
        # Build KDTree
        self.kdtree = cKDTree(projected_coords)
        
        logger.info(
            f"Spatial index built with {len(self.node_ids)} nodes, "
            f"UTM zone {utm_zone}S"
        )
    
    def find_nearest_node(
        self,
        lat: float,
        lng: float,
        max_snap_distance_m: float = 2000.0
    ) -> Optional[SnapResult]:
        """
        Find the nearest graph node to a given coordinate.
        
        Args:
            lat: Latitude in decimal degrees
            lng: Longitude in decimal degrees
            max_snap_distance_m: Maximum snap distance in metres (default: 2km)
        
        Returns:
            SnapResult with node_id and distance, or None if beyond max distance
        
        Raises:
            RuntimeError: If spatial index is not initialized
        """
        if self.kdtree is None:
            raise RuntimeError("Spatial index not initialized")
        
        # Project query point to UTM
        query_point = self._project_to_utm(
            np.array([lat]),
            np.array([lng]),
            self.crs_info['utm_zone']
        )[0]
        
        # Query KDTree
        distance, idx = self.kdtree.query(query_point, k=1)
        
        if distance > max_snap_distance_m:
            logger.debug(
                f"Point ({lat}, {lng}) is {distance:.1f}m from nearest node, "
                f"exceeds max_snap_distance_m ({max_snap_distance_m}m)"
            )
            return None
        
        node_id = self.node_ids[idx]
        node_data = self.nodes[node_id]
        
        return SnapResult(
            node_id=node_id,
            snap_distance_m=distance,
            node_lat=node_data['lat'],
            node_lng=node_data['lng']
        )
    
    def _get_utm_zone(self, lat: float, lng: float) -> int:
        """
        Determine UTM zone from longitude.
        Harare is at ~31°E, which is UTM zone 36.
        """
        utm_zone = int((lng + 180) / 6) + 1
        return utm_zone
    
    def _project_to_utm(
        self,
        lats: np.ndarray,
        lngs: np.ndarray,
        utm_zone: int
    ) -> np.ndarray:
        """
        Project lat/lng coordinates to UTM using approximate formulas.
        This is a simplified projection suitable for local distance queries.
        
        For production use, consider using pyproj for accurate transformations.
        """
        # Simplified UTM projection approximation
        # This is adequate for local distance queries within a city
        
        # Central meridian for the UTM zone
        central_meridian = (utm_zone - 1) * 6 - 180 + 3  # -180 to +180
        
        # Convert to radians
        lat_rad = np.radians(lats)
        lng_rad = np.radians(lngs)
        central_meridian_rad = np.radians(central_meridian)
        
        # UTM parameters (WGS84)
        a = 6378137.0  # Semi-major axis
        e = 0.081819190842622  # Eccentricity
        k0 = 0.9996  # Scale factor
        
        # Calculate UTM coordinates
        n = a / np.sqrt(1 - e**2 * np.sin(lat_rad)**2)
        t = np.tan(lat_rad)**2
        c = e**2 * np.cos(lat_rad)**2 / (1 - e**2)
        a_coeff = (lng_rad - central_meridian_rad) * np.cos(lat_rad)
        
        # M: meridional arc
        M = a * (
            (1 - e**2 / 4 - 3 * e**4 / 64 - 5 * e**6 / 256) * lat_rad
            - (3 * e**2 / 8 + 3 * e**4 / 32 + 45 * e**6 / 1024) * np.sin(2 * lat_rad)
            + (15 * e**4 / 256 + 45 * e**6 / 1024) * np.sin(4 * lat_rad)
            - (35 * e**6 / 3072) * np.sin(6 * lat_rad)
        )
        
        # Easting (x)
        x = k0 * n * (
            a_coeff
            + (1 - t + c) * a_coeff**3 / 6
            + (5 - 18 * t + t**2 + 72 * c - 58 * e**2) * a_coeff**5 / 120
        ) + 500000  # False easting
        
        # Northing (y) - southern hemisphere adjustment
        y = k0 * (
            M
            + n * np.tan(lat_rad) * (
                a_coeff**2 / 2
                + (5 - t + 9 * c + 4 * c**2) * a_coeff**4 / 24
                + (61 - 58 * t + t**2 + 600 * c - 330 * e**2) * a_coeff**6 / 720
            )
        )
        
        # Adjust for southern hemisphere (Harare is in southern hemisphere)
        if np.mean(lats) < 0:
            y = y + 10000000  # False northing for southern hemisphere
        
        return np.column_stack([x, y])


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate Haversine distance between two points in metres.
    Used as fallback for distance calculations when UTM projection is not available.
    
    Args:
        lat1, lng1: First point coordinates
        lat2, lng2: Second point coordinates
    
    Returns:
        Distance in metres
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Earth radius in metres
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c
