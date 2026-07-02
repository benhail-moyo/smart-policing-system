# Phase 4: Patrol Optimization Engine

> **Prerequisite:** Phase 3 complete. Hotspots exist in the database.  
> **Estimated time:** 8–10 hours (the most complex phase)  
> **This phase is done when:** `POST /patrol/compare` returns results for both Dijkstra and GA with all 5 metrics, and the fuel saving percentage is calculable.

---

## Context for Claude

This is the most academically significant module in Crime-Watch. The dissertation claims a ≥15% reduction in fuel consumption — this is where that claim is either proven or not.

Two algorithms are implemented and compared:
1. **Dijkstra's Algorithm** — deterministic shortest-path baseline
2. **Genetic Algorithm (GA)** — stochastic multi-objective optimizer

The `compare_algorithms()` method in `route_engine.py` generates the data that goes into your dissertation Chapter 4 results table. Get this right.

Existing files to complete:
- `backend/app/services/routing/route_engine.py` — orchestrator, needs `_save_route()` verified
- `backend/app/services/routing/dijkstra_solver.py` — needs validation
- `backend/app/services/routing/genetic_solver.py` — needs fitness curve export fixed
- `backend/app/api/v1/routes/patrol.py` — endpoints exist, need hardening

---

## What Needs to Be Built in This Phase

### 4.1 Validate and Complete the Dijkstra Solver

The existing solver implements nearest-neighbor tour construction with Dijkstra for inter-node paths. This is correct but needs:

**Add edge case handling:**
```python
def solve(self) -> List[Tuple[float, float]]:
    # Edge cases
    if len(self.waypoints) == 0:
        return []
    if len(self.waypoints) == 1:
        return self.waypoints
    if len(self.waypoints) == 2:
        return self.waypoints  # Only one possible route

    # ... existing nearest-neighbor implementation ...
```

**Add a method to explain the route for the API response:**
```python
def get_tour_explanation(self, tour_indices: list) -> list:
    """Returns human-readable waypoint sequence for debugging/dissertation."""
    return [
        {"step": i+1, "lat": self.waypoints[idx][0], "lng": self.waypoints[idx][1]}
        for i, idx in enumerate(tour_indices)
    ]
```

**Important dissertation note to code comment:**
```python
# DISSERTATION CONTEXT:
# This is NOT a full Dijkstra optimization of the TSP.
# It is a GREEDY NEAREST-NEIGHBOR HEURISTIC that uses Dijkstra
# to resolve shortest paths between nodes.
# TSP is NP-hard (no polynomial solution exists).
# Our nearest-neighbor heuristic provides a baseline in O(n²) time.
# The GA attempts to improve upon this baseline.
# This distinction MUST be clear in Chapter 3.
```

### 4.2 Validate and Complete the Genetic Algorithm Solver

The existing GA solver uses DEAP with Ordered Crossover. Verify these critical details:

**Fix the DEAP global state issue:**
DEAP registers classes globally. In pytest, if `creator.FitnessMin` is created twice, it throws a warning/error. The existing guard `if not hasattr(creator, "FitnessMin")` handles this — verify it works in your test suite.

**Export convergence data to a file (required for dissertation):**
```python
def save_convergence_data(self, output_path: str = None):
    """
    Saves GA fitness curve to JSON for dissertation Figure 4.X.
    Call this after solve() in the benchmark runner.
    """
    import json
    from pathlib import Path
    
    if output_path is None:
        output_path = f"ml/routing/benchmarks/results/convergence_{int(time.time())}.json"
    
    data = {
        "generations": list(range(len(self.fitness_history))),
        "fitness": self.fitness_history,
        "parameters": {
            "pop_size": self.pop_size,
            "generations": self.generations,
            "mutation_rate": self.mutation_rate,
            "crossover_rate": self.crossover_rate,
            "alpha": self.alpha,
            "seed": 42
        }
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return output_path
```

**Add a parameter sensitivity test:**
```python
def parameter_sensitivity_analysis(waypoints, weights, output_dir="ml/routing/benchmarks/results/"):
    """
    Tests different GA configurations. Run once for dissertation.
    Generates data for a parameter sensitivity table in Chapter 3.
    """
    configs = [
        {"pop_size": 50,  "generations": 100, "mutation_rate": 0.02},
        {"pop_size": 100, "generations": 200, "mutation_rate": 0.02},  # Default
        {"pop_size": 200, "generations": 200, "mutation_rate": 0.02},
        {"pop_size": 100, "generations": 200, "mutation_rate": 0.05},
        {"pop_size": 100, "generations": 300, "mutation_rate": 0.01},
    ]
    
    results = []
    for config in configs:
        solver = GeneticSolver(waypoints=waypoints, hotspot_weights=weights, **config)
        import time
        start = time.perf_counter()
        route = solver.solve()
        elapsed = (time.perf_counter() - start) * 1000
        
        from math import radians, sin, cos, sqrt, atan2
        dist = _total_distance(route)
        results.append({**config, "distance_km": dist, "time_ms": round(elapsed, 1)})
    
    return results
```

### 4.3 Complete the RouteEngine

The existing `route_engine.py` is mostly complete. Add:

**Fuel consumption model based on route quality:**
```python
# More sophisticated fuel model
# Accounts for stop-start in urban patrol (not pure highway driving)
FUEL_CONSUMPTION_L_PER_KM_URBAN = 0.15   # 15L/100km urban patrol
FUEL_CONSUMPTION_L_PER_KM_HIGHWAY = 0.10  # 10L/100km between zones
```

For the proof-of-concept, use the urban figure (0.15) consistently and document it.

**Add historical route retrieval:**
```python
@patrol_bp.get("/routes")
@jwt_required()
def get_recent_routes():
    """Returns recent patrol routes for comparison display."""
    routes = (
        db.session.query(PatrolRoute)
        .order_by(PatrolRoute.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify([{
        "id": r.id,
        "algorithm": r.algorithm,
        "created_at": r.created_at.isoformat(),
        "total_distance_km": r.total_distance_km,
        "estimated_fuel_litres": r.estimated_fuel_litres,
        "estimated_time_minutes": r.estimated_time_minutes,
        "hotspots_covered": r.hotspots_covered,
        "computation_time_ms": r.computation_time_ms,
    } for r in routes]), 200
```

### 4.4 Dissertation Results Endpoint

This endpoint is specifically designed to produce structured data for Chapter 4.

**In `patrol.py`:**
```python
@patrol_bp.post("/compare")
@jwt_required()
def compare_algorithms():
    """
    ACADEMIC ENDPOINT — Runs both algorithms on the same hotspot set.
    Response structure maps directly to the Chapter 4 comparison table.
    
    Request: { "hotspot_ids": [1, 2, 3, 4, 5] }
    
    Response:
    {
      "dijkstra": {
        "total_distance_km": float,
        "estimated_fuel_litres": float,
        "estimated_time_minutes": float,
        "hotspots_covered": int,
        "computation_time_ms": float
      },
      "genetic": { ... same fields ... },
      "comparison": {
        "fuel_saving_genetic_vs_dijkstra_pct": float,
        "distance_saving_pct": float,
        "speed_advantage_dijkstra_ms": float,
        "verdict": "GA achieves X% fuel reduction at Y% computation cost"
      }
    }
    """
```

The `verdict` string should be auto-generated from the comparison metrics. Example:
```python
verdict = (
    f"GA achieves {abs(fuel_pct):.1f}% {'fuel reduction' if fuel_pct > 0 else 'fuel increase'} "
    f"vs Dijkstra, at {speed_diff:.0f}ms additional computation time."
)
```

---

## Acceptance Checklist

```bash
# 0. Ensure hotspots exist in DB from Phase 3 seed data
curl http://localhost:5000/api/v1/hotspots/ -H "Authorization: Bearer <token>"
# Note the hotspot IDs returned (e.g. [1,2,3,4,5])

# 1. Single algorithm - Dijkstra
curl -X POST http://localhost:5000/api/v1/patrol/optimize \
  -H "Authorization: Bearer <officer_token>" \
  -H "Content-Type: application/json" \
  -d '{"hotspot_ids": [1,2,3,4,5], "algorithm": "dijkstra", "start_lat": -17.8292, "start_lng": 31.0522}'
# Expected: route with waypoints, all 5 metrics populated, computation_time_ms < 50

# 2. Single algorithm - Genetic
# Same request but algorithm: "genetic"
# Expected: route with waypoints, computation_time_ms > dijkstra (GA is slower)

# 3. THE CRITICAL TEST - Compare both
curl -X POST http://localhost:5000/api/v1/patrol/compare \
  -H "Authorization: Bearer <officer_token>" \
  -H "Content-Type: application/json" \
  -d '{"hotspot_ids": [1,2,3,4,5]}'
# Expected:
# - dijkstra and genetic both have values
# - comparison.fuel_saving_genetic_vs_dijkstra_pct is a number (positive = GA better)
# - comparison.speed_advantage_dijkstra_ms is positive (Dijkstra faster)
# - verdict string is human-readable

# 4. Recent routes saved to DB
curl http://localhost:5000/api/v1/patrol/routes \
  -H "Authorization: Bearer <token>"
# Expected: array of 2 recent routes (one per algorithm from test 3)

# 5. Empty hotspot list handled gracefully
curl -X POST http://localhost:5000/api/v1/patrol/optimize \
  -d '{"hotspot_ids": [], "algorithm": "dijkstra"}'
# Expected: 400 { "error": "No valid hotspots found..." }
```

---

## Dissertation Notes for This Phase

**Chapter 3 — Algorithm Design (Dijkstra):**

Formally present the algorithm and your application context:
- Standard Dijkstra operates on a weighted graph G=(V,E)
- In Crime-Watch: V = hotspot centroids + patrol base, E = all pairs connected by Haversine distance
- The patrol routing problem is a variant of the Travelling Salesman Problem (TSP)
- Our approach: nearest-neighbor heuristic using Dijkstra edge weights → O(n²) construction
- Limitation: greedy heuristic, guaranteed to be within 25% of optimal for Euclidean instances

**Chapter 3 — Algorithm Design (Genetic Algorithm):**

Key parameters to document in a table:
| Parameter | Value | Justification |
|---|---|---|
| Population size | 100 | Balances diversity vs computation time |
| Generations | 200 | Convergence observed at ~150 generations (cite your plot) |
| Crossover operator | Ordered Crossover (OX) | Standard for permutation encoding |
| Mutation operator | Shuffle Indexes | Preserves permutation validity |
| Tournament size | 3 | Mild selection pressure, maintains diversity |
| Seed | 42 | Ensures reproducibility |

**Chapter 4 — Results to present:**
- Comparison table: Dijkstra vs GA across all 4 benchmark scenarios
- GA convergence plot (Figure 4.X): fitness vs generations → shows algorithm learning
- Bar chart: computation time comparison (Figure 4.Y)
- The fuel saving percentage is your headline result

**Connecting to Objective 3:**
> "To develop a patrol optimization engine... aiming for a 15% reduction in resource consumption"

Your result either supports or refutes this target. Both outcomes are academically valid — what matters is rigorous measurement and honest discussion.

---

## What You Learn in This Phase

- **Graph theory applied:** NetworkX is an industry-standard graph library. Everything from Google Maps to logistics software uses graph algorithms.
- **Evolutionary algorithms:** GA is a class of algorithms inspired by natural selection. Used in portfolio optimization, scheduling, drug discovery, neural architecture search. Understanding DEAP is a transferable skill.
- **Benchmarking methodology:** Running algorithms on multiple scenarios of varying size and averaging results is the scientific method applied to software. This is how real performance claims are validated.
- **The NP-hard problem:** TSP is NP-hard. This means no known polynomial algorithm solves it exactly. Your dissertation demonstrates awareness of computational complexity — a senior-level understanding.
