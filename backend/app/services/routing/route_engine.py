"""
Patrol Route Optimization Engine
==================================
Orchestrates both routing algorithms and produces a side-by-side
comparison for academic benchmarking.

DISSERTATION NOTE:
  This is the most academically significant module.
  The compare_algorithms() method generates your Chapter 4 results table.
  Every metric here (distance, fuel, time, computation_time_ms) must be
  reported and discussed in your dissertation.

ARCHITECTURE DECISION — Why two algorithms?
  Dijkstra: deterministic, guaranteed shortest path, fast computation.
             Good baseline. Limitation: finds shortest distance, not
             necessarily best coverage of weighted hotspots.
  Genetic Algorithm: stochastic, finds near-optimal solution in
             combinatorially large search space. Slower but can
             optimize for multiple objectives simultaneously (distance
             AND hotspot coverage AND fuel).
  Academic value: demonstrating this tradeoff IS the contribution.

MULTI-VEHICLE EXTENSION:
  The optimize_multi_vehicle() method adds geographic pre-partitioning
  for multi-vehicle scenarios while reusing existing single-vehicle GA/Dijkstra
  logic unchanged. This is a heuristic decoupling approach, not joint VRP optimization.
"""
import time
import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from geoalchemy2.shape import to_shape

from app.models.models import Hotspot
from app import db

logger = logging.getLogger(__name__)


@dataclass
class RouteResult:
    """Comparable output from either algorithm."""
    algorithm: str
    waypoints: list          # List of (lat, lng) tuples
    total_distance_km: float
    estimated_fuel_litres: float
    estimated_time_minutes: float
    hotspots_covered: int
    computation_time_ms: float
    hotspot_ids: list
    route_explanation: list = field(default_factory=list)
    convergence_file: Optional[str] = None


class RouteEngine:
    """
    Orchestrator: takes hotspots, runs both algorithms, saves results.
    """

    # Fuel model for urban stop-start patrol conditions.
    FUEL_CONSUMPTION_L_PER_KM_URBAN = 0.15   # 15L/100km
    FUEL_CONSUMPTION_L_PER_KM_HIGHWAY = 0.10  # Documented for future mixed routing.
    FUEL_CONSUMPTION_L_PER_KM = FUEL_CONSUMPTION_L_PER_KM_URBAN
    AVERAGE_SPEED_KMH = 40            # Urban patrol speed

    def optimize(
        self,
        hotspot_ids: List[str],
        algorithm: str = "both",
        start_location: Optional[tuple] = None,
        save_to_db: bool = False
    ) -> List[RouteResult]:
        """
        Run route optimization.

        Args:
            hotspot_ids: IDs of hotspots to include in the patrol.
            algorithm: 'dijkstra' | 'genetic' | 'both'
            start_location: (lat, lng) of patrol start point (police station).
            save_to_db: Whether to persist results to database (default: False to avoid duplicate saves)

        Returns:
            List of RouteResult objects (1 or 2 depending on algorithm param).
        """
        algorithm = str(algorithm or "both").lower()
        if algorithm not in ("dijkstra", "genetic", "both"):
            raise ValueError("algorithm must be one of: dijkstra, genetic, both")

        requested_ids = list(dict.fromkeys(str(hotspot_id) for hotspot_id in hotspot_ids))
        hotspots_by_id = {
            str(hotspot.hotspot_id): hotspot
            for hotspot in db.session.query(Hotspot).filter(Hotspot.hotspot_id.in_(requested_ids)).all()
        }
        hotspots = [hotspots_by_id[hotspot_id] for hotspot_id in requested_ids if hotspot_id in hotspots_by_id]
        if not hotspots:
            raise ValueError("No valid hotspots found for provided IDs")

        waypoints = self._hotspots_to_waypoints(hotspots)
        if start_location:
            waypoints = [start_location] + waypoints

        results = []

        if algorithm in ("dijkstra", "both"):
            results.append(self._run_dijkstra(waypoints, hotspots))

        if algorithm in ("genetic", "both"):
            results.append(self._run_genetic(waypoints, hotspots))

        # Only persist results to DB if explicitly requested
        if save_to_db:
            for result in results:
                self._save_route(result)

        return results

    def optimize_multi_vehicle(
        self,
        hotspot_ids: List[str],
        vehicle_count: int,
        depot_locations: Optional[List[tuple]] = None,
        algorithm: str = "both",
        start_location: Optional[tuple] = None,
        save_to_db: bool = False
    ) -> Dict[str, Any]:
        """
        Run multi-vehicle route optimization with geographic pre-partitioning.
        
        This method implements a heuristic decoupling approach:
        1. Geographically partition hotspots among vehicles (KMeans clustering)
        2. Run existing single-vehicle GA/Dijkstra independently on each partition
        3. Return N labeled route results
        
        IMPORTANT: This does NOT perform joint VRP optimization. Partition assignment
        and route ordering are decoupled. Load imbalance across vehicles is expected.
        
        Args:
            hotspot_ids: IDs of hotspots to include in the patrol.
            vehicle_count: Number of vehicles to partition among.
            depot_locations: Optional list of (lat, lng) for each vehicle's starting point.
                          If None, assumes single depot (all vehicles from same location).
                          If provided, must have length == vehicle_count.
            algorithm: 'dijkstra' | 'genetic' | 'both'
            start_location: (lat, lng) of patrol start point (used if depot_locations is None).
            save_to_db: Whether to persist results to database.
        
        Returns:
            Dict with:
            - 'generation_id': UUID grouping all routes from this request
            - 'vehicle_count': Number of vehicles
            - 'routes': List of route results, each with vehicle_id
            - 'partition_metadata': Information about partition sizes and fallback usage
        
        Raises:
            ValueError: If vehicle_count <= 0 or other validation fails
        """
        algorithm = str(algorithm or "both").lower()
        if algorithm not in ("dijkstra", "genetic", "both"):
            raise ValueError("algorithm must be one of: dijkstra, genetic, both")
        
        # Regression requirement: N=1 must behave identically to single-vehicle system
        if vehicle_count == 1:
            logger.info("Single vehicle requested - using existing single-vehicle path")
            single_results = self.optimize(
                hotspot_ids,
                algorithm=algorithm,
                start_location=start_location,
                save_to_db=save_to_db
            )
            
            # Wrap in multi-vehicle response format for consistency
            generation_id = str(uuid.uuid4())
            wrapped_routes = []
            for result in single_results:
                route_dict = self._result_to_dict(result)
                route_dict['vehicle_id'] = 1
                route_dict['generation_id'] = generation_id
                wrapped_routes.append(route_dict)
            
            return {
                'generation_id': generation_id,
                'vehicle_count': 1,
                'routes': wrapped_routes,
                'partition_metadata': {
                    'partition_sizes': [len(hotspot_ids)],
                    'fallback_used': False,
                    'load_imbalance': 0.0
                }
            }
        
        # Validate and load hotspots
        requested_ids = list(dict.fromkeys(str(hotspot_id) for hotspot_id in hotspot_ids))
        hotspots_by_id = {
            str(hotspot.hotspot_id): hotspot
            for hotspot in db.session.query(Hotspot).filter(Hotspot.hotspot_id.in_(requested_ids)).all()
        }
        hotspots = [hotspots_by_id[hotspot_id] for hotspot_id in requested_ids if hotspot_id in hotspots_by_id]
        
        if not hotspots:
            raise ValueError("No valid hotspots found for provided IDs")
        
        # Extract hotspot centroids
        hotspot_centroids = self._hotspots_to_waypoints(hotspots)
        
        # Determine depot locations
        if depot_locations is None:
            # Single depot: all vehicles start from same location
            if start_location:
                depot_locations = [start_location] * vehicle_count
            else:
                # Use centroid of all hotspots as default start
                avg_lat = sum(h[0] for h in hotspot_centroids) / len(hotspot_centroids)
                avg_lng = sum(h[1] for h in hotspot_centroids) / len(hotspot_centroids)
                depot_locations = [(avg_lat, avg_lng)] * vehicle_count
                logger.info(f"No start_location provided, using hotspot centroid: ({avg_lat:.4f}, {avg_lng:.4f})")
        
        # Partition hotspots
        from .partitioning import HotspotPartitioner
        partitioner = HotspotPartitioner(random_state=42)
        partition_result = partitioner.partition_hotspots(
            hotspot_centroids,
            vehicle_count,
            depot_locations=depot_locations
        )
        
        # Log partition metadata for dissertation validation
        logger.info(
            f"Partition complete: sizes={partition_result.partition_sizes}, "
            f"fallback_used={partition_result.fallback_used}"
        )
        
        # Calculate load imbalance metric
        if partition_result.partition_sizes:
            max_size = max(partition_result.partition_sizes)
            min_size = min(partition_result.partition_sizes)
            load_imbalance = (max_size - min_size) / max(len(hotspots), 1) if max_size > 0 else 0.0
        else:
            load_imbalance = 0.0
        
        # Run routing for each vehicle's partition
        generation_id = str(uuid.uuid4())
        all_routes = []
        
        for vehicle_id, vehicle_hotspot_indices in enumerate(partition_result.vehicle_groups):
            if not vehicle_hotspot_indices:
                # Vehicle assigned zero hotspots - return empty route
                logger.warning(f"Vehicle {vehicle_id} assigned zero hotspots")
                empty_route = {
                    'vehicle_id': vehicle_id,
                    'generation_id': generation_id,
                    'algorithm': algorithm,
                    'waypoints': [],
                    'total_distance_km': 0.0,
                    'estimated_fuel_litres': 0.0,
                    'estimated_time_minutes': 0.0,
                    'hotspots_covered': 0,
                    'computation_time_ms': 0.0,
                    'hotspot_ids': [],
                    'geometry': None,
                    'empty_route': True
                }
                all_routes.append(empty_route)
                continue
            
            # Map partition indices back to original hotspot objects
            # Create a mapping from centroid to hotspot
            centroid_to_hotspot = {centroid: hotspot for centroid, hotspot in zip(hotspot_centroids, hotspots)}
            vehicle_hotspots = [centroid_to_hotspot[centroid] for centroid in vehicle_hotspot_indices]
            vehicle_hotspot_ids = [str(h.hotspot_id) for h in vehicle_hotspots]
            
            # Build waypoints for this vehicle
            vehicle_waypoints = vehicle_hotspot_indices
            vehicle_depot = depot_locations[vehicle_id] if depot_locations else start_location
            if vehicle_depot:
                vehicle_waypoints = [vehicle_depot] + vehicle_waypoints
            
            # Run existing single-vehicle routing
            vehicle_results = []
            if algorithm in ("dijkstra", "both"):
                vehicle_results.append(self._run_dijkstra(vehicle_waypoints, vehicle_hotspots))
            
            if algorithm in ("genetic", "both"):
                vehicle_results.append(self._run_genetic(vehicle_waypoints, vehicle_hotspots))
            
            # Convert to dict format and add vehicle metadata
            for result in vehicle_results:
                route_dict = self._result_to_dict(result)
                route_dict['vehicle_id'] = vehicle_id
                route_dict['generation_id'] = generation_id
                all_routes.append(route_dict)
            
            # Save to database if requested
            if save_to_db:
                for result in vehicle_results:
                    result_dict = self._result_to_dict(result)
                    self._save_multi_vehicle_route(
                        result_dict,
                        vehicle_id=vehicle_id,
                        generation_id=generation_id
                    )
        
        return {
            'generation_id': generation_id,
            'vehicle_count': vehicle_count,
            'routes': all_routes,
            'partition_metadata': {
                'partition_sizes': partition_result.partition_sizes,
                'fallback_used': partition_result.fallback_used,
                'load_imbalance': round(load_imbalance, 3)
            }
        }

    def compare_algorithms(
        self,
        hotspot_ids: List[str],
        start_location: Optional[tuple] = None,
    ) -> dict:
        """
        Runs both algorithms and returns a structured comparison dict.
        This output maps directly to your dissertation results table.
        """
        results = self.optimize(
            hotspot_ids,
            algorithm="both",
            start_location=start_location,
        )
        dijkstra = next((r for r in results if r.algorithm == "dijkstra"), None)
        genetic = next((r for r in results if r.algorithm == "genetic"), None)

        if not dijkstra or not genetic:
            return {}

        fuel_saving_pct = (
            (dijkstra.estimated_fuel_litres - genetic.estimated_fuel_litres)
            / dijkstra.estimated_fuel_litres * 100
        ) if dijkstra.estimated_fuel_litres > 0 else 0
        distance_saving_pct = (
            (dijkstra.total_distance_km - genetic.total_distance_km)
            / dijkstra.total_distance_km * 100
        ) if dijkstra.total_distance_km > 0 else 0
        speed_diff = genetic.computation_time_ms - dijkstra.computation_time_ms
        verdict = (
            f"GA achieves {abs(fuel_saving_pct):.1f}% "
            f"{'fuel reduction' if fuel_saving_pct > 0 else 'fuel increase'} "
            f"vs Dijkstra, at {max(speed_diff, 0):.0f}ms additional computation time."
        )

        return {
            "dijkstra": self._result_to_dict(dijkstra),
            "genetic": self._result_to_dict(genetic),
            "comparison": {
                "fuel_saving_genetic_vs_dijkstra_pct": round(fuel_saving_pct, 2),
                "distance_saving_pct": round(distance_saving_pct, 2),
                "speed_advantage_dijkstra_ms": round(
                    speed_diff, 2
                ),
                "coverage_advantage_genetic": (
                    genetic.hotspots_covered - dijkstra.hotspots_covered
                ),
                "verdict": verdict,
            },
        }

    def _run_dijkstra(self, waypoints: list, hotspots: List[Hotspot]) -> RouteResult:
        from app.services.routing.dijkstra_solver import DijkstraSolver
        start = time.perf_counter()
        solver = DijkstraSolver(waypoints)
        route = solver.solve()
        elapsed_ms = (time.perf_counter() - start) * 1000

        distance = self._calculate_total_distance(route)
        return RouteResult(
            algorithm="dijkstra",
            waypoints=route,
            total_distance_km=distance,
            estimated_fuel_litres=distance * self.FUEL_CONSUMPTION_L_PER_KM,
            estimated_time_minutes=distance / self.AVERAGE_SPEED_KMH * 60,
            hotspots_covered=len(hotspots),
            computation_time_ms=elapsed_ms,
            hotspot_ids=[str(h.hotspot_id) for h in hotspots],
            route_explanation=solver.get_tour_explanation(),
        )

    def _run_genetic(self, waypoints: list, hotspots: List[Hotspot]) -> RouteResult:
        try:
            from app.services.routing.genetic_solver import GeneticSolver
            from flask import current_app

            start = time.perf_counter()
            weights = [h.risk_score for h in hotspots]
            if len(waypoints) > len(hotspots):
                weights = [0.0] + weights
            solver = GeneticSolver(
                waypoints=waypoints,
                hotspot_weights=weights,
                pop_size=current_app.config.get("GA_POPULATION_SIZE", 100),
                generations=current_app.config.get("GA_GENERATIONS", 200),
                mutation_rate=current_app.config.get("GA_MUTATION_RATE", 0.02),
                crossover_rate=current_app.config.get("GA_CROSSOVER_RATE", 0.8),
            )
            route = solver.solve()
            elapsed_ms = (time.perf_counter() - start) * 1000

            distance = self._calculate_total_distance(route)
            return RouteResult(
                algorithm="genetic",
                waypoints=route,
                total_distance_km=distance,
                estimated_fuel_litres=distance * self.FUEL_CONSUMPTION_L_PER_KM,
                estimated_time_minutes=distance / self.AVERAGE_SPEED_KMH * 60,
                hotspots_covered=len(hotspots),
                computation_time_ms=elapsed_ms,
                hotspot_ids=[str(h.hotspot_id) for h in hotspots],
                route_explanation=[
                    {"step": step + 1, "lat": point[0], "lng": point[1]}
                    for step, point in enumerate(route)
                ],
                convergence_file=solver.save_convergence_data(),
            )
        except ImportError as imp_err:
            logger.warning("GeneticSolver unavailable: %s — falling back to Dijkstra route", imp_err)
            # Fall back to deterministic baseline
            return self._run_dijkstra(waypoints, hotspots)
        except Exception as exc:
            logger.exception("Genetic solver failed: %s", exc)
            # Fall back to deterministic baseline on any GA failure
            return self._run_dijkstra(waypoints, hotspots)

    def _hotspots_to_waypoints(self, hotspots: List[Hotspot]) -> list:
        from geoalchemy2.shape import to_shape
        waypoints = []
        for h in hotspots:
            try:
                geom = to_shape(h.centroid)
                lat = geom.y
                lng = geom.x
                waypoints.append((float(lat), float(lng)))
            except Exception:
                continue
        return waypoints

    def _calculate_total_distance(self, waypoints: list) -> float:
        """Haversine distance across all waypoints in km."""
        from math import radians, sin, cos, sqrt, atan2
        total = 0.0
        for i in range(len(waypoints) - 1):
            lat1, lng1 = waypoints[i]
            lat2, lng2 = waypoints[i + 1]
            R = 6371  # Earth radius km
            dlat = radians(lat2 - lat1)
            dlng = radians(lng2 - lng1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
            total += R * 2 * atan2(sqrt(a), sqrt(1 - a))
        return round(total, 3)

    def _save_route(self, result: RouteResult):
        from app.models.models import PatrolRoute
        route = PatrolRoute(
            algorithm=result.algorithm,
            waypoints=[{"lat": lat, "lng": lng} for lat, lng in result.waypoints],
            total_distance_km=result.total_distance_km,
            estimated_fuel_litres=result.estimated_fuel_litres,
            estimated_time_minutes=result.estimated_time_minutes,
            hotspots_covered=result.hotspots_covered,
            computation_time_ms=result.computation_time_ms,
            hotspot_ids=result.hotspot_ids,
        )
        db.session.add(route)
        db.session.commit()
    
    def _save_multi_vehicle_route(
        self,
        result_dict: dict,
        vehicle_id: int,
        generation_id: str
    ):
        """
        Save a multi-vehicle route with vehicle identification.
        
        Args:
            result_dict: Route result dictionary from _result_to_dict
            vehicle_id: Vehicle identifier (0-indexed)
            generation_id: UUID grouping all routes from this request
        """
        try:
            from app.models.models import PatrolRoute
            
            # Handle empty routes (vehicles with zero hotspots)
            if result_dict.get('empty_route'):
                logger.info(f"Skipping save for empty route (vehicle {vehicle_id})")
                return
                
            route = PatrolRoute(
                algorithm=result_dict.get('algorithm'),
                waypoints=result_dict.get('waypoints', []),
                total_distance_km=result_dict.get('total_distance_km', 0),
                estimated_fuel_litres=result_dict.get('estimated_fuel_litres', 0),
                estimated_time_minutes=result_dict.get('estimated_time_minutes', 0),
                hotspots_covered=result_dict.get('hotspots_covered', 0),
                computation_time_ms=result_dict.get('computation_time_ms', 0),
                hotspot_ids=result_dict.get('hotspot_ids', []),
                vehicle_id=vehicle_id,
                generation_id=generation_id
            )
            db.session.add(route)
            db.session.commit()
            logger.info(f"Saved route for vehicle {vehicle_id} in generation {generation_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save multi-vehicle route: {e}")
            raise

    def _result_to_dict(self, r: RouteResult) -> dict:
        # Generate simple GeoJSON LineString from waypoints for straight-line routes
        geometry = None
        if r.waypoints and len(r.waypoints) >= 2:
            geometry = {
                "type": "LineString",
                "coordinates": [[point[1], point[0]] for point in r.waypoints]  # [lng, lat]
            }
        
        return {
            "algorithm": r.algorithm,
            "total_distance_km": r.total_distance_km,
            "estimated_fuel_litres": r.estimated_fuel_litres,
            "estimated_time_minutes": r.estimated_time_minutes,
            "hotspots_covered": r.hotspots_covered,
            "computation_time_ms": r.computation_time_ms,
            "hotspot_ids": r.hotspot_ids,
            "waypoints": [
                {"lat": point[0], "lng": point[1]}
                for point in r.waypoints
            ],
            "route_explanation": r.route_explanation,
            "convergence_file": r.convergence_file,
            "geometry": geometry
        }


route_engine = RouteEngine()
