"""
Algorithm Benchmarking Module
================================
Standalone script that runs both routing algorithms against
multiple test scenarios and outputs a CSV/JSON results table.

This is your dissertation Chapter 4 data generator.
Run this INDEPENDENTLY of the Flask app to produce clean results.

Usage:
    cd crime-watch/
    python -m ml.routing.benchmarks.run_benchmarks

Output:
    ml/routing/benchmarks/results/benchmark_results.csv
    ml/routing/benchmarks/results/ga_convergence_[scenario].json
"""
import csv
import json
import time
import random
import os
from dataclasses import dataclass, asdict
from typing import List, Tuple
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "backend"))

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


@dataclass
class BenchmarkScenario:
    name: str
    waypoints: List[Tuple[float, float]]
    weights: List[float]


@dataclass
class BenchmarkResult:
    scenario: str
    algorithm: str
    total_distance_km: float
    computation_time_ms: float
    # Dijkstra won't have these — GA specific
    final_fitness: float = 0.0
    generations_to_converge: int = 0


def generate_harare_scenarios() -> List[BenchmarkScenario]:
    """
    Generate test scenarios of varying complexity around Harare.
    Scenarios: 5, 10, 15, 20 hotspot waypoints.
    Using realistic Harare lat/lng coordinates.
    """
    random.seed(42)
    # Harare urban bbox
    LAT_RANGE = (-17.95, -17.70)
    LNG_RANGE = (30.95, 31.20)

    scenarios = []
    for n_points in [5, 10, 15, 20]:
        waypoints = [
            (
                random.uniform(*LAT_RANGE),
                random.uniform(*LNG_RANGE),
            )
            for _ in range(n_points)
        ]
        weights = [random.uniform(0.1, 1.0) for _ in range(n_points)]
        scenarios.append(BenchmarkScenario(
            name=f"harare_{n_points}_hotspots",
            waypoints=waypoints,
            weights=weights,
        ))

    return scenarios


def run_dijkstra_benchmark(scenario: BenchmarkScenario) -> BenchmarkResult:
    from app.services.routing.dijkstra_solver import DijkstraSolver
    start = time.perf_counter()
    solver = DijkstraSolver(scenario.waypoints)
    route = solver.solve()
    elapsed_ms = (time.perf_counter() - start) * 1000
    distance = _total_distance(route)

    return BenchmarkResult(
        scenario=scenario.name,
        algorithm="dijkstra",
        total_distance_km=distance,
        computation_time_ms=round(elapsed_ms, 3),
    )


def run_genetic_benchmark(scenario: BenchmarkScenario) -> BenchmarkResult:
    from app.services.routing.genetic_solver import GeneticSolver
    start = time.perf_counter()
    solver = GeneticSolver(
        waypoints=scenario.waypoints,
        hotspot_weights=scenario.weights,
        pop_size=100,
        generations=200,
    )
    route = solver.solve()
    elapsed_ms = (time.perf_counter() - start) * 1000
    distance = _total_distance(route)

    # Save convergence data for dissertation plot
    convergence_path = RESULTS_DIR / f"ga_convergence_{scenario.name}.json"
    with open(convergence_path, "w") as f:
        json.dump({"fitness_history": solver.fitness_history}, f)

    return BenchmarkResult(
        scenario=scenario.name,
        algorithm="genetic",
        total_distance_km=distance,
        computation_time_ms=round(elapsed_ms, 3),
        final_fitness=solver.fitness_history[-1] if solver.fitness_history else 0,
        generations_to_converge=len(solver.fitness_history),
    )


def _total_distance(waypoints: list) -> float:
    total = 0.0
    for i in range(len(waypoints) - 1):
        lat1, lng1 = waypoints[i]
        lat2, lng2 = waypoints[i + 1]
        R = 6371
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
        total += R * 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(total, 3)


def run_all_benchmarks():
    print("=" * 60)
    print("Crime-Watch Algorithm Benchmarking Suite")
    print("=" * 60)

    scenarios = generate_harare_scenarios()
    results = []

    for scenario in scenarios:
        print(f"\nScenario: {scenario.name} ({len(scenario.waypoints)} waypoints)")

        print("  Running Dijkstra...", end=" ")
        dijk_result = run_dijkstra_benchmark(scenario)
        print(f"{dijk_result.computation_time_ms:.1f}ms | {dijk_result.total_distance_km}km")
        results.append(dijk_result)

        print("  Running Genetic Algorithm...", end=" ")
        ga_result = run_genetic_benchmark(scenario)
        print(f"{ga_result.computation_time_ms:.1f}ms | {ga_result.total_distance_km}km")
        results.append(ga_result)

        # Print comparison
        improvement = (
            (dijk_result.total_distance_km - ga_result.total_distance_km)
            / dijk_result.total_distance_km * 100
        )
        speed_diff = ga_result.computation_time_ms - dijk_result.computation_time_ms
        print(f"  GA distance improvement: {improvement:.1f}%")
        print(f"  Dijkstra speed advantage: {speed_diff:.1f}ms faster")

    # Export CSV
    csv_path = RESULTS_DIR / "benchmark_results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows([asdict(r) for r in results])

    print(f"\n✓ Results saved to {csv_path}")
    print(f"✓ GA convergence plots saved to {RESULTS_DIR}/")
    return results


if __name__ == "__main__":
    run_all_benchmarks()
