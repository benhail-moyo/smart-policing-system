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
"""
import time
import logging
from dataclasses import dataclass
from typing import List, Optional

from app.models.models import Hotspot, PatrolRoute
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


class RouteEngine:
    """
    Orchestrator: takes hotspots, runs both algorithms, saves results.
    """

    # Fuel consumption estimate: average ZRP patrol vehicle
    FUEL_CONSUMPTION_L_PER_KM = 0.12  # 12L/100km
    AVERAGE_SPEED_KMH = 40            # Urban patrol speed

    def optimize(
        self,
        hotspot_ids: List[int],
        algorithm: str = "both",
        start_location: Optional[tuple] = None,
    ) -> List[RouteResult]:
        """
        Run route optimization.

        Args:
            hotspot_ids: IDs of hotspots to include in the patrol.
            algorithm: 'dijkstra' | 'genetic' | 'both'
            start_location: (lat, lng) of patrol start point (police station).

        Returns:
            List of RouteResult objects (1 or 2 depending on algorithm param).
        """
        hotspots = db.session.query(Hotspot).filter(Hotspot.id.in_(hotspot_ids)).all()
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

        # Persist results to DB for history and dissertation data export
        for result in results:
            self._save_route(result)

        return results

    def compare_algorithms(self, hotspot_ids: List[int]) -> dict:
        """
        Runs both algorithms and returns a structured comparison dict.
        This output maps directly to your dissertation results table.
        """
        results = self.optimize(hotspot_ids, algorithm="both")
        dijkstra = next((r for r in results if r.algorithm == "dijkstra"), None)
        genetic = next((r for r in results if r.algorithm == "genetic"), None)

        if not dijkstra or not genetic:
            return {}

        fuel_saving_pct = (
            (dijkstra.estimated_fuel_litres - genetic.estimated_fuel_litres)
            / dijkstra.estimated_fuel_litres * 100
        ) if dijkstra.estimated_fuel_litres > 0 else 0

        return {
            "dijkstra": self._result_to_dict(dijkstra),
            "genetic": self._result_to_dict(genetic),
            "comparison": {
                "fuel_saving_genetic_vs_dijkstra_pct": round(fuel_saving_pct, 2),
                "speed_advantage_dijkstra_ms": round(
                    genetic.computation_time_ms - dijkstra.computation_time_ms, 2
                ),
                "coverage_advantage_genetic": (
                    genetic.hotspots_covered - dijkstra.hotspots_covered
                ),
            },
        }

    def _run_dijkstra(self, waypoints: list, hotspots: List[Hotspot]) -> RouteResult:
        from app.services.routing.dijkstra_solver import DijkstraSolver
        start = time.time()
        solver = DijkstraSolver(waypoints)
        route = solver.solve()
        elapsed_ms = (time.time() - start) * 1000

        distance = self._calculate_total_distance(route)
        return RouteResult(
            algorithm="dijkstra",
            waypoints=route,
            total_distance_km=distance,
            estimated_fuel_litres=distance * self.FUEL_CONSUMPTION_L_PER_KM,
            estimated_time_minutes=distance / self.AVERAGE_SPEED_KMH * 60,
            hotspots_covered=len(hotspots),
            computation_time_ms=elapsed_ms,
            hotspot_ids=[h.id for h in hotspots],
        )

    def _run_genetic(self, waypoints: list, hotspots: List[Hotspot]) -> RouteResult:
        from app.services.routing.genetic_solver import GeneticSolver
        from flask import current_app
        start = time.time()
        solver = GeneticSolver(
            waypoints=waypoints,
            hotspot_weights=[h.risk_score for h in hotspots],
            pop_size=current_app.config.get("GA_POPULATION_SIZE", 100),
            generations=current_app.config.get("GA_GENERATIONS", 200),
            mutation_rate=current_app.config.get("GA_MUTATION_RATE", 0.02),
            crossover_rate=current_app.config.get("GA_CROSSOVER_RATE", 0.8),
        )
        route = solver.solve()
        elapsed_ms = (time.time() - start) * 1000

        distance = self._calculate_total_distance(route)
        return RouteResult(
            algorithm="genetic",
            waypoints=route,
            total_distance_km=distance,
            estimated_fuel_litres=distance * self.FUEL_CONSUMPTION_L_PER_KM,
            estimated_time_minutes=distance / self.AVERAGE_SPEED_KMH * 60,
            hotspots_covered=len(hotspots),
            computation_time_ms=elapsed_ms,
            hotspot_ids=[h.id for h in hotspots],
        )

    def _hotspots_to_waypoints(self, hotspots: List[Hotspot]) -> list:
        from geoalchemy2.shape import to_shape
        waypoints = []
        for h in hotspots:
            if h.centroid:
                pt = to_shape(h.centroid)
                waypoints.append((pt.y, pt.x))  # (lat, lng)
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
        from shapely.geometry import LineString
        from geoalchemy2.shape import from_shape
        line = LineString([(lng, lat) for lat, lng in result.waypoints])
        route = PatrolRoute(
            algorithm=result.algorithm,
            route_geometry=from_shape(line, srid=4326),
            total_distance_km=result.total_distance_km,
            estimated_fuel_litres=result.estimated_fuel_litres,
            estimated_time_minutes=result.estimated_time_minutes,
            hotspots_covered=result.hotspots_covered,
            computation_time_ms=result.computation_time_ms,
            hotspot_ids=result.hotspot_ids,
        )
        db.session.add(route)
        db.session.commit()

    def _result_to_dict(self, r: RouteResult) -> dict:
        return {
            "algorithm": r.algorithm,
            "total_distance_km": r.total_distance_km,
            "estimated_fuel_litres": r.estimated_fuel_litres,
            "estimated_time_minutes": r.estimated_time_minutes,
            "hotspots_covered": r.hotspots_covered,
            "computation_time_ms": r.computation_time_ms,
        }


route_engine = RouteEngine()
