"""
Geographic partitioning module for multi-vehicle patrol routing.
Supports both single-depot and multi-depot scenarios using KMeans clustering.
"""
import logging
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


@dataclass
class PartitionResult:
    """Result of hotspot partitioning."""
    vehicle_groups: List[List[Tuple[float, float]]]  # List of hotspot groups per vehicle
    vehicle_assignments: Dict[int, int]  # hotspot_index -> vehicle_id mapping
    partition_sizes: List[int]  # Number of hotspots per vehicle
    fallback_used: bool = False


class HotspotPartitioner:
    """
    Partitions hotspot centroids among multiple patrol vehicles using geographic clustering.
    
    Supports both single-depot (all vehicles from same location) and multi-depot scenarios.
    For multi-depot, clustering is weighted toward each vehicle's starting point.
    """
    
    def __init__(self, random_state: Optional[int] = None):
        """
        Initialize partitioner.
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
    
    def partition_hotspots(
        self,
        hotspots: List[Tuple[float, float]],
        vehicle_count: int,
        depot_locations: Optional[List[Tuple[float, float]]] = None
    ) -> PartitionResult:
        """
        Partition hotspots among vehicles using geographic clustering.
        
        Args:
            hotspots: List of (lat, lng) tuples for hotspot centroids
            vehicle_count: Number of vehicles to partition among
            depot_locations: Optional list of (lat, lng) for each vehicle's starting point.
                          If None, assumes single depot (geographic clustering only).
                          If provided, must have length == vehicle_count.
        
        Returns:
            PartitionResult with vehicle groups and assignment metadata
        
        Raises:
            ValueError: If vehicle_count <= 0 or hotspots is empty
        """
        # Validation
        if vehicle_count <= 0:
            raise ValueError(f"vehicle_count must be positive, got {vehicle_count}")
        
        if not hotspots:
            logger.warning("No hotspots provided for partitioning")
            return PartitionResult(
                vehicle_groups=[[] for _ in range(vehicle_count)],
                vehicle_assignments={},
                fallback_used=False,
                partition_sizes=[0] * vehicle_count
            )
        
        # Edge case: N=1 - return all hotspots as single group
        if vehicle_count == 1:
            logger.info("Single vehicle requested - skipping partitioning")
            return PartitionResult(
                vehicle_groups=[hotspots],
                vehicle_assignments={i: 0 for i in range(len(hotspots))},
                fallback_used=False,
                partition_sizes=[len(hotspots)]
            )
        
        # Edge case: N >= hotspot_count - some vehicles will get 0-1 hotspots
        if vehicle_count >= len(hotspots):
            logger.warning(
                f"Vehicle count ({vehicle_count}) >= hotspot count ({len(hotspots)}). "
                "Some vehicles will receive zero or one hotspots."
            )
            # Simple round-robin assignment
            return self._round_robin_partition(hotspots, vehicle_count)
        
        # Validate depot locations if provided
        if depot_locations is not None:
            if len(depot_locations) != vehicle_count:
                raise ValueError(
                    f"depot_locations length ({len(depot_locations)}) must match "
                    f"vehicle_count ({vehicle_count})"
                )
        
        # Attempt KMeans clustering
        try:
            return self._kmeans_partition(hotspots, vehicle_count, depot_locations)
        except Exception as e:
            logger.error(f"KMeans partitioning failed: {e}. Falling back to round-robin.")
            return self._round_robin_partition(hotspots, vehicle_count, fallback_used=True)
    
    def _kmeans_partition(
        self,
        hotspots: List[Tuple[float, float]],
        vehicle_count: int,
        depot_locations: Optional[List[Tuple[float, float]]] = None
    ) -> PartitionResult:
        """
        Partition using appropriate method based on depot scenario.
        
        For multi-depot scenarios: uses nearest-depot assignment (each hotspot assigned to closest depot).
        For single-depot scenarios: uses KMeans clustering for geographic partitioning.
        """
        # Multi-depot: use nearest-depot assignment
        if depot_locations is not None:
            return self._nearest_depot_partition(hotspots, vehicle_count, depot_locations)
        
        # Single-depot: use KMeans clustering
        return self._single_depot_kmeans_partition(hotspots, vehicle_count)
    
    def _nearest_depot_partition(
        self,
        hotspots: List[Tuple[float, float]],
        vehicle_count: int,
        depot_locations: List[Tuple[float, float]]
    ) -> PartitionResult:
        """
        Partition using nearest-depot assignment for multi-depot scenarios.
        
        Each hotspot is assigned to the vehicle whose depot is closest in distance.
        This is the correct approach for multi-depot routing where vehicles start
        from different locations.
        """
        from math import radians, sin, cos, sqrt, atan2
        
        def haversine_distance(lat1, lng1, lat2, lng2):
            """Calculate Haversine distance between two points in km."""
            R = 6371  # Earth radius km
            dlat = radians(lat2 - lat1)
            dlng = radians(lng2 - lng1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
            return R * 2 * atan2(sqrt(a), sqrt(1 - a))
        
        # Build vehicle groups
        vehicle_groups = [[] for _ in range(vehicle_count)]
        vehicle_assignments = {}
        
        for hotspot_idx, hotspot in enumerate(hotspots):
            # Find nearest depot
            distances = []
            for depot_id, depot in enumerate(depot_locations):
                dist = haversine_distance(hotspot[0], hotspot[1], depot[0], depot[1])
                distances.append((dist, depot_id))
            
            # Assign to closest depot
            _, closest_depot_id = min(distances, key=lambda x: x[0])
            vehicle_groups[closest_depot_id].append(hotspot)
            vehicle_assignments[hotspot_idx] = closest_depot_id
        
        partition_sizes = [len(group) for group in vehicle_groups]
        
        logger.info(
            f"Nearest-depot partitioning complete. Sizes: {partition_sizes}. "
            f"Load imbalance: max={max(partition_sizes)}, min={min(partition_sizes)}"
        )
        
        return PartitionResult(
            vehicle_groups=vehicle_groups,
            vehicle_assignments=vehicle_assignments,
            fallback_used=False,
            partition_sizes=partition_sizes
        )
    
    def _single_depot_kmeans_partition(
        self,
        hotspots: List[Tuple[float, float]],
        vehicle_count: int
    ) -> PartitionResult:
        """
        Partition using KMeans clustering for single-depot scenarios.
        
        All vehicles start from the same location, so geographic clustering
        is appropriate to partition the area among vehicles.
        """
        # Convert to numpy array
        hotspot_array = np.array(hotspots)
        
        # Use KMeans++ initialization for single-depot
        logger.info(f"Single-depot partitioning: using KMeans++ initialization")
        
        # Run KMeans
        kmeans = KMeans(
            n_clusters=vehicle_count,
            init='k-means++',
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )
        
        labels = kmeans.fit_predict(hotspot_array)
        
        # Check for degenerate clustering (e.g., all points in one cluster)
        unique_labels = np.unique(labels)
        if len(unique_labels) < vehicle_count:
            logger.warning(
                f"KMeans produced degenerate output ({len(unique_labels)} clusters vs {vehicle_count} requested). "
                "This may indicate duplicate hotspot coordinates. Falling back to round-robin."
            )
            return self._round_robin_partition(hotspots, vehicle_count, fallback_used=True)
        
        # Build vehicle groups
        vehicle_groups = [[] for _ in range(vehicle_count)]
        vehicle_assignments = {}
        
        for hotspot_idx, label in enumerate(labels):
            vehicle_groups[label].append(hotspots[hotspot_idx])
            vehicle_assignments[hotspot_idx] = int(label)
        
        partition_sizes = [len(group) for group in vehicle_groups]
        
        logger.info(
            f"KMeans partitioning complete. Sizes: {partition_sizes}. "
            f"Load imbalance: max={max(partition_sizes)}, min={min(partition_sizes)}"
        )
        
        return PartitionResult(
            vehicle_groups=vehicle_groups,
            vehicle_assignments=vehicle_assignments,
            fallback_used=False,
            partition_sizes=partition_sizes
        )
    
    def _round_robin_partition(
        self,
        hotspots: List[Tuple[float, float]],
        vehicle_count: int,
        fallback_used: bool = False
    ) -> PartitionResult:
        """
        Simple round-robin assignment as fallback.
        
        Used when:
        - N >= hotspot_count
        - KMeans fails or produces degenerate output
        """
        vehicle_groups = [[] for _ in range(vehicle_count)]
        vehicle_assignments = {}
        
        for hotspot_idx, hotspot in enumerate(hotspots):
            vehicle_id = hotspot_idx % vehicle_count
            vehicle_groups[vehicle_id].append(hotspot)
            vehicle_assignments[hotspot_idx] = vehicle_id
        
        partition_sizes = [len(group) for group in vehicle_groups]
        
        if fallback_used:
            logger.warning(
                f"Round-robin fallback used. Sizes: {partition_sizes}. "
                "This may produce suboptimal geographic clustering."
            )
        else:
            logger.info(f"Round-robin assignment (N >= hotspot_count). Sizes: {partition_sizes}")
        
        return PartitionResult(
            vehicle_groups=vehicle_groups,
            vehicle_assignments=vehicle_assignments,
            fallback_used=fallback_used,
            partition_sizes=partition_sizes
        )
