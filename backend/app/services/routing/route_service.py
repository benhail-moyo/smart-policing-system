"""
Route service for input validation, snapping, pairwise path calculation,
geometry stitching, and response construction.
"""
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RouteRequest:
    """Validated route request."""
    city: str
    start_lat: float
    start_lng: float
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None
    stops: Optional[List[Tuple[float, float]]] = None
    algorithm: str = 'dijkstra'
    return_to_start: bool = False
    seed: Optional[int] = None
    ga_config: Optional[Dict[str, Any]] = None


@dataclass
class RouteResponse:
    """Standardized route response."""
    algorithm: str
    total_distance_m: float
    nodes_visited: int
    execution_time_ms: float
    start_snap_distance_m: float
    end_snap_distance_m: float
    geometry: Dict[str, Any]  # GeoJSON LineString
    # Additional fields for multi-stop routes
    order: Optional[List[int]] = None
    seed_used: Optional[int] = None
    generations: Optional[int] = None
    convergence: Optional[List[float]] = None


class RouteService:
    """
    Service for handling routing requests with validation, snapping,
    and path computation using road network graph.
    """
    
    def __init__(self, max_snap_distance_m: Optional[float] = None):
        """
        Initialize route service.
        
        Args:
            max_snap_distance_m: Maximum distance for snapping points to graph (default from config)
        """
        # Lazy load config to avoid circular imports
        from app.config.routing_config import routing_config
        self.max_snap_distance_m = max_snap_distance_m or routing_config.max_snap_distance_m
        self._spatial_index: Optional[SpatialIndex] = None
        self._graph: Optional[Dict] = None
        self._nodes: Optional[Dict] = None
    
    def _ensure_loaded(self):
        """Ensure graph and spatial index are loaded."""
        if self._graph is None or self._spatial_index is None:
            from .graph_store import graph_store
            from .spatial_index import SpatialIndex
            self._graph, self._nodes = graph_store.get_graph()
            self._spatial_index = SpatialIndex(self._nodes)
    
    def validate_point_to_point_request(self, data: Dict) -> RouteRequest:
        """
        Validate and parse point-to-point route request.
        
        Args:
            data: Request JSON data
        
        Returns:
            RouteRequest with validated fields
        
        Raises:
            ValueError: If validation fails
        """
        if not data:
            raise ValueError("Request body is required")
        
        city = data.get('city', 'harare')
        if city != 'harare':
            raise ValueError(f"Only 'harare' city is supported, got '{city}'")
        
        start = data.get('start')
        if not start or 'lat' not in start or 'lng' not in start:
            raise ValueError("Valid 'start' object with 'lat' and 'lng' is required")
        
        end = data.get('end')
        if not end or 'lat' not in end or 'lng' not in end:
            raise ValueError("Valid 'end' object with 'lat' and 'lng' is required")
        
        algorithm = data.get('algorithm', 'dijkstra')
        if algorithm not in ('dijkstra',):
            raise ValueError(f"Algorithm must be 'dijkstra', got '{algorithm}'")
        
        return RouteRequest(
            city=city,
            start_lat=float(start['lat']),
            start_lng=float(start['lng']),
            end_lat=float(end['lat']),
            end_lng=float(end['lng']),
            algorithm=algorithm
        )
    
    def validate_multi_stop_request(self, data: Dict) -> RouteRequest:
        """
        Validate and parse multi-stop route request.
        
        Args:
            data: Request JSON data
        
        Returns:
            RouteRequest with validated fields
        
        Raises:
            ValueError: If validation fails
        """
        from app.config.routing_config import routing_config

        if not data:
            raise ValueError("Request body is required")
        
        city = data.get('city', 'harare')
        if city != 'harare':
            raise ValueError(f"Only 'harare' city is supported, got '{city}'")
        
        start = data.get('start')
        if not start or 'lat' not in start or 'lng' not in start:
            raise ValueError("Valid 'start' object with 'lat' and 'lng' is required")
        
        stops = data.get('stops')
        if not stops or not isinstance(stops, list):
            raise ValueError("Valid 'stops' array with at least 3 points is required")
        
        if len(stops) < 3:
            raise ValueError(f"At least 3 stops are required, got {len(stops)}")
        
        # Validate each stop
        validated_stops = []
        for i, stop in enumerate(stops):
            if not isinstance(stop, dict) or 'lat' not in stop or 'lng' not in stop:
                raise ValueError(f"Stop {i} must be an object with 'lat' and 'lng'")
            validated_stops.append((float(stop['lat']), float(stop['lng'])))
        
        return_to_start = data.get('return_to_start', False)
        seed = data.get('seed')
        
        # Parse GA config with server-side limits
        ga_config_raw = data.get('ga_config', {})
        ga_config = {
            'population_size': min(
                max(int(ga_config_raw.get('population_size', routing_config.ga_population_size)), 
                    routing_config.ga_min_population_size), 
                routing_config.ga_max_population_size
            ),
            'generations': min(
                max(int(ga_config_raw.get('generations', routing_config.ga_generations)), 
                    routing_config.ga_min_generations), 
                routing_config.ga_max_generations
            ),
            'mutation_rate': min(
                max(float(ga_config_raw.get('mutation_rate', routing_config.ga_mutation_rate)), 
                    routing_config.ga_min_mutation_rate), 
                routing_config.ga_max_mutation_rate
            ),
            'crossover_rate': min(
                max(float(ga_config_raw.get('crossover_rate', routing_config.ga_crossover_rate)), 
                    routing_config.ga_min_crossover_rate), 
                routing_config.ga_max_crossover_rate
            ),
            'seed': seed
        }
        
        return RouteRequest(
            city=city,
            start_lat=float(start['lat']),
            start_lng=float(start['lng']),
            stops=validated_stops,
            algorithm='compare',  # Multi-stop always uses comparison
            return_to_start=return_to_start,
            seed=seed,
            ga_config=ga_config
        )
    
    def compute_point_to_point_route(self, request: RouteRequest) -> RouteResponse:
        """
        Compute point-to-point route using Dijkstra.
        
        Args:
            request: Validated route request
        
        Returns:
            RouteResponse with geometry and metrics
        
        Raises:
            RuntimeError: If graph loading fails
            ValueError: If snapping fails or no route exists
        """
        self._ensure_loaded()
        
        # Snap start and end points
        start_snap = self._snap_point(request.start_lat, request.start_lng)
        if not start_snap:
            raise ValueError(
                f"Start point ({request.start_lat}, {request.start_lng}) is too far "
                f"from road network (> {self.max_snap_distance_m}m)"
            )
        
        end_snap = self._snap_point(request.end_lat, request.end_lng)
        if not end_snap:
            raise ValueError(
                f"End point ({request.end_lat}, {request.end_lng}) is too far "
                f"from road network (> {self.max_snap_distance_m}m)"
            )
        
        # Run Dijkstra (lazy import)
        from .algorithms.dijkstra import dijkstra
        result = dijkstra(self._graph, start_snap.node_id, end_snap.node_id)
        
        if result.status == 'no_route':
            raise ValueError("No route exists between the snapped points in the road network")
        
        # Reconstruct geometry
        geometry = self._reconstruct_geometry(result.path_node_ids, result.edge_keys)
        
        return RouteResponse(
            algorithm=request.algorithm,
            total_distance_m=result.total_distance_m,
            nodes_visited=result.nodes_visited,
            execution_time_ms=result.execution_time_ms,
            start_snap_distance_m=start_snap.snap_distance_m,
            end_snap_distance_m=end_snap.snap_distance_m,
            geometry=geometry
        )
    
    def compute_multi_stop_comparison(self, request: RouteRequest) -> Dict[str, Any]:
        """
        Compute multi-stop route comparison between baseline and GA.
        
        Args:
            request: Validated multi-stop route request
        
        Returns:
            Dict with baseline and genetic results comparison
        
        Raises:
            RuntimeError: If graph loading fails
            ValueError: If snapping fails or no route exists between stops
        """
        self._ensure_loaded()
        
        # Lazy import dependencies
        from .algorithms.dijkstra import dijkstra
        from .algorithms.genetic_algorithm import GeneticAlgorithm, GAConfig, nearest_neighbour_ordering
        from app.config.routing_config import routing_config
        
        # Snap all points
        all_points = [(request.start_lat, request.start_lng)] + request.stops
        snapped_points = []
        
        for i, (lat, lng) in enumerate(all_points):
            snap = self._snap_point(lat, lng)
            if not snap:
                raise ValueError(
                    f"Point {i} ({lat}, {lng}) is too far from road network "
                    f"(> {self.max_snap_distance_m}m)"
                )
            snapped_points.append(snap)
        
        # Build pairwise distance matrix using Dijkstra
        num_points = len(snapped_points)
        distance_matrix = [[0.0] * num_points for _ in range(num_points)]
        path_matrix = [[None] * num_points for _ in range(num_points)]
        
        for i in range(num_points):
            for j in range(num_points):
                if i == j:
                    continue
                
                start_node = snapped_points[i].node_id
                end_node = snapped_points[j].node_id
                
                result = dijkstra(self._graph, start_node, end_node)
                
                if result.status == 'no_route':
                    raise ValueError(
                        f"No route exists between point {i} and point {j} in the road network"
                    )
                
                distance_matrix[i][j] = result.total_distance_m
                path_matrix[i][j] = result
        
        # Compute baseline (nearest-neighbor)
        baseline_order = nearest_neighbour_ordering(distance_matrix)
        baseline_distance = self._calculate_route_distance(baseline_order, distance_matrix)
        baseline_geometry = self._stitch_route_geometry(baseline_order, path_matrix)
        
        # Add return to start if requested
        if request.return_to_start:
            baseline_order.append(baseline_order[0])
            baseline_distance += distance_matrix[baseline_order[-2]][baseline_order[-1]]
            # Extend geometry with return segment
            return_segment = path_matrix[baseline_order[-2]][baseline_order[-1]]
            if return_segment:
                baseline_geometry = self._merge_geometries(baseline_geometry, return_segment)
        
        # Compute GA optimization
        ga_config = GAConfig(**request.ga_config)
        ga = GeneticAlgorithm(distance_matrix, ga_config)
        ga_result = ga.solve()
        
        ga_distance = ga_result.best_distance
        ga_order = ga_result.best_order
        
        # Add return to start if requested
        if request.return_to_start:
            ga_order.append(ga_order[0])
            ga_distance += distance_matrix[ga_order[-2]][ga_order[-1]]
        
        ga_geometry = self._stitch_route_geometry(ga_order, path_matrix)
        
        # Add return segment geometry if requested
        if request.return_to_start:
            return_segment = path_matrix[ga_order[-2]][ga_order[-1]]
            if return_segment:
                ga_geometry = self._merge_geometries(ga_geometry, return_segment)
        
        # Calculate savings
        distance_saving_pct = (
            (baseline_distance - ga_distance) / baseline_distance * 100
            if baseline_distance > 0 else 0
        )
        
        # Fuel proxy (using same assumptions as existing system)
        fuel_consumption_l_per_km = routing_config.fuel_consumption_l_per_km_urban
        baseline_fuel = baseline_distance / 1000 * fuel_consumption_l_per_km
        ga_fuel = ga_distance / 1000 * fuel_consumption_l_per_km
        fuel_saving_pct = (
            (baseline_fuel - ga_fuel) / baseline_fuel * 100
            if baseline_fuel > 0 else 0
        )
        
        return {
            'baseline': {
                'algorithm': 'dijkstra_nearest_neighbour',
                'order': baseline_order,
                'total_distance_m': baseline_distance,
                'execution_time_ms': 0,  # Baseline is deterministic and fast
                'geometry': baseline_geometry
            },
            'genetic': {
                'algorithm': 'genetic_algorithm',
                'order': ga_order,
                'total_distance_m': ga_distance,
                'execution_time_ms': ga_result.execution_time_ms,
                'seed': ga_result.seed_used,
                'generations': ga_result.generations_completed,
                'convergence': ga_result.convergence_history,
                'geometry': ga_geometry
            },
            'comparison': {
                'distance_saving_pct': round(distance_saving_pct, 2),
                'fuel_proxy_saving_pct': round(fuel_saving_pct, 2),
                'fuel_consumption_l_per_km': fuel_consumption_l_per_km
            }
        }
    
    def _snap_point(self, lat: float, lng: float) -> Optional['SnapResult']:
        """Snap a point to the nearest graph node."""
        if self._spatial_index is None:
            raise RuntimeError("Spatial index not initialized")
        return self._spatial_index.find_nearest_node(lat, lng, self.max_snap_distance_m)
    
    def _reconstruct_geometry(
        self,
        path_node_ids: List[int],
        edge_keys: List[Tuple[int, int, int]]
    ) -> Dict[str, Any]:
        """
        Reconstruct GeoJSON LineString geometry from path.
        
        Args:
            path_node_ids: Ordered list of node IDs
            edge_keys: List of (u, v, key) edge identifiers
        
        Returns:
            GeoJSON LineString geometry with [lng, lat] coordinates
        """
        return {
            'type': 'LineString',
            'coordinates': self._build_path_coordinates(path_node_ids, edge_keys)
        }

    def _build_path_coordinates(
        self,
        path_node_ids: List[int],
        edge_keys: List[Tuple[int, int, int]]
    ) -> List[List[float]]:
        """Build a LineString in traversal order, including each edge shape."""
        if not path_node_ids:
            return []

        coordinates: List[List[float]] = []
        if not edge_keys:
            return self._node_coordinate(path_node_ids[0]) or []

        for u, v, key in edge_keys:
            u_coordinate = self._node_coordinate(u)
            v_coordinate = self._node_coordinate(v)
            if u_coordinate:
                self._append_coordinate(coordinates, u_coordinate)

            edge = next(
                (
                    candidate for candidate in self._graph.get(u, [])
                    if candidate['v'] == v and candidate.get('key') == key
                ),
                None,
            )
            edge_geometry = edge.get('geometry_latlng', []) if edge else []
            if edge_geometry:
                # Stored as [lat, lng]; orient it from u to v before converting
                # to GeoJSON's [lng, lat]. Some OSM geometries are reversed.
                geometry = [[point[1], point[0]] for point in edge_geometry]
                if u_coordinate and v_coordinate and self._geometry_is_reversed(
                    geometry, u_coordinate, v_coordinate
                ):
                    geometry.reverse()
                for coordinate in geometry:
                    self._append_coordinate(coordinates, coordinate)

            if v_coordinate:
                self._append_coordinate(coordinates, v_coordinate)

        return coordinates

    def _node_coordinate(self, node_id: int) -> Optional[List[float]]:
        node_data = self._nodes.get(node_id)
        if not node_data:
            return None
        return [node_data['lng'], node_data['lat']]

    @staticmethod
    def _append_coordinate(coordinates: List[List[float]], coordinate: List[float]) -> None:
        if not coordinates or coordinates[-1] != coordinate:
            coordinates.append(coordinate)

    @staticmethod
    def _geometry_is_reversed(
        geometry: List[List[float]], start: List[float], end: List[float]
    ) -> bool:
        """Return whether geometry's endpoints better match end-to-start."""
        def squared_distance(a: List[float], b: List[float]) -> float:
            return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

        forward = squared_distance(geometry[0], start) + squared_distance(geometry[-1], end)
        reverse = squared_distance(geometry[-1], start) + squared_distance(geometry[0], end)
        return reverse < forward
    
    def _stitch_route_geometry(
        self,
        order: List[int],
        path_matrix: List[List[Any]]
    ) -> Dict[str, Any]:
        """
        Stitch together edge geometries for a multi-stop route.
        
        Args:
            order: Ordered list of point indices
            path_matrix: Matrix of Dijkstra results between all pairs
        
        Returns:
            GeoJSON LineString geometry
        """
        all_coordinates = []
        
        for i in range(len(order) - 1):
            from_idx = order[i]
            to_idx = order[i + 1]
            
            path_result = path_matrix[from_idx][to_idx]
            if path_result and path_result.path_node_ids:
                segment_coordinates = self._build_path_coordinates(
                    path_result.path_node_ids, path_result.edge_keys
                )
                for coordinate in segment_coordinates:
                    self._append_coordinate(all_coordinates, coordinate)
        
        # Remove adjacent duplicates
        return {
            'type': 'LineString',
            'coordinates': all_coordinates
        }
    
    def _merge_geometries(
        self,
        geom1: Dict[str, Any],
        geom2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two LineString geometries."""
        coords1 = geom1.get('coordinates', [])
        coords2 = geom2.get('coordinates', [])
        
        merged = coords1 + coords2
        
        # Remove potential duplicate at merge point
        deduped = []
        for coord in merged:
            if not deduped or coord != deduped[-1]:
                deduped.append(coord)
        
        return {
            'type': 'LineString',
            'coordinates': deduped
        }
    
    def _calculate_route_distance(self, order: List[int], distance_matrix: List[List[float]]) -> float:
        """Calculate total distance for a route order."""
        total = 0.0
        for i in range(len(order) - 1):
            from_idx = order[i]
            to_idx = order[i + 1]
            total += distance_matrix[from_idx][to_idx]
        return total


# Global service instance (lazy initialization)
route_service = None

def get_route_service():
    """Get or create the route service instance."""
    global route_service
    if route_service is None:
        route_service = RouteService()
    return route_service
