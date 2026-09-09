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
        Partition using KMeans clustering with optional depot initialization.
        
        For multi-depot scenarios, initializes cluster centers near depot locations
        to bias clustering toward each vehicle's starting point.
        """
        # Convert to numpy array
        hotspot_array = np.array(hotspots)
        
        # Initialize cluster centers
        if depot_locations is not None:
            # Multi-depot: initialize near depot locations
            init_centers = np.array(depot_locations)
            logger.info(f"Multi-depot partitioning: initializing {vehicle_count} clusters near depot locations")
        else:
            # Single-depot: use KMeans++ initialization
            init_centers = 'k-means++'
            logger.info(f"Single-depot partitioning: using KMeans++ initialization")
        
        # Run KMeans
        kmeans = KMeans(
            n_clusters=vehicle_count,
            init=init_centers,
            random_state=self.random_state,
            n_init=10 if depot_locations is None else 1,
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
