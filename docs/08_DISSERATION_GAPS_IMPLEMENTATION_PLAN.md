# Dissertation Gaps Implementation Plan

> **Purpose**: This document outlines the identified gaps between current implementation and dissertation objectives, providing clear implementation plans for each gap.
> **Target Audience**: Developer (Benhail Moyo) implementing academic evaluation features
> **Status**: Implementation pending

---

## Overview

This document addresses the critical gaps preventing the Crime-Watch system from meeting dissertation evaluation requirements. Each gap includes:
- **Objective**: Why this feature is needed for the dissertation
- **Current State**: What exists today
- **Implementation Plan**: Step-by-step implementation guidance
- **Success Criteria**: How to verify completion

---

## Gap 1: Routing Benchmark Statistical Analysis

### Objective
Enable rigorous academic comparison of Dijkstra vs Genetic Algorithm routing by implementing statistical averaging across multiple runs. This is required for dissertation Chapter 4 to demonstrate:
- Statistical validity of results (mean ± standard deviation)
- Reproducibility of findings
- Proper handling of GA stochasticity

### Current State
- <ref_file file="C:\smart-policing-system\ml\routing\benchmarks\run_benchmarks.py" /> runs single iterations per scenario
- No statistical averaging (N_RUNS)
- No standard deviation calculations
- CSV output format incomplete for dissertation requirements
- No fuel improvement percentage calculations

### Implementation Plan

#### Step 1: Add Statistical Averaging Function
**File**: `ml/routing/benchmarks/run_benchmarks.py`

```python
N_RUNS = 5  # Run each scenario 5 times for statistical validity

def run_with_averaging(scenario, algorithm_fn, n_runs=N_RUNS):
    """
    Runs the algorithm N times and returns averaged metrics.
    GA is stochastic — results vary slightly each run even with seed=42
    because scenario waypoints are randomized per run.
    Dijkstra is deterministic — same result every run.
    
    Returns: dict with mean ± std_dev for dissertation reporting
    """
    distances = []
    times = []
    fuel_litres = []
    
    for i in range(n_runs):
        result = algorithm_fn(scenario)
        distances.append(result.total_distance_km)
        times.append(result.computation_time_ms)
        fuel_litres.append(result.estimated_fuel_litres)
    
    import statistics
    return {
        "mean_distance_km": statistics.mean(distances),
        "std_distance_km": statistics.stdev(distances) if n_runs > 1 else 0,
        "mean_time_ms": statistics.mean(times),
        "std_time_ms": statistics.stdev(times) if n_runs > 1 else 0,
        "mean_fuel_litres": statistics.mean(fuel_litres),
        "std_fuel_litres": statistics.stdev(fuel_litres) if n_runs > 1 else 0,
    }
```

#### Step 2: Add Fuel Improvement Calculation
**File**: `ml/routing/benchmarks/run_benchmarks.py`

```python
def calculate_fuel_improvement(dijkstra_result, ga_result) -> float:
    """
    Returns percentage by which GA reduces fuel vs Dijkstra.
    Positive = GA is better.
    Target: ≥15% to meet dissertation objective.
    """
    if dijkstra_result.estimated_fuel_litres == 0:
        return 0.0
    return (
        (dijkstra_result.estimated_fuel_litres - ga_result.estimated_fuel_litres)
        / dijkstra_result.estimated_fuel_litres * 100
    )
```

#### Step 3: Update CSV Export Format
**File**: `ml/routing/benchmarks/run_benchmarks.py`

Update the CSV writer to produce dissertation-required format:

```python
csv_headers = [
    "scenario",
    "algorithm",
    "n_waypoints",
    "mean_distance_km",
    "std_distance_km",
    "mean_time_ms",
    "std_time_ms",
    "mean_fuel_litres",
    "std_fuel_litres",
    "improvement_pct_vs_dijkstra"
]
```

Example output:
```
scenario,algorithm,n_waypoints,mean_distance_km,std_distance_km,mean_time_ms,std_time_ms,mean_fuel_litres,std_fuel_litres,improvement_pct_vs_dijkstra
harare_5_hotspots,dijkstra,5,12.3,0.0,2.1,0.0,1.85,0.0,0.0
harare_5_hotspots,genetic,5,10.8,0.4,145.2,8.3,1.62,0.08,12.4
harare_10_hotspots,dijkstra,10,28.5,0.0,5.8,0.0,4.28,0.0,0.0
harare_10_hotspots,genetic,10,24.2,0.6,380.5,15.2,3.63,0.09,15.2
```

#### Step 4: Update Main Benchmark Loop
**File**: `ml/routing/benchmarks/run_benchmarks.py`

Modify `run_all_benchmarks()` to use `run_with_averaging()`:

```python
def run_all_benchmarks():
    scenarios = generate_harare_scenarios()
    results = []

    for scenario in scenarios:
        print(f"\nScenario: {scenario.name} ({len(scenario.waypoints)} waypoints)")

        # Run Dijkstra with averaging
        dijk_result = run_with_averaging(scenario, run_dijkstra_benchmark)
        print(f"  Dijkstra: {dijk_result['mean_distance_km']:.1f}km ± {dijk_result['std_distance_km']:.2f}")

        # Run GA with averaging
        ga_result = run_with_averaging(scenario, run_genetic_benchmark)
        print(f"  GA: {ga_result['mean_distance_km']:.1f}km ± {ga_result['std_distance_km']:.2f}")

        # Calculate fuel improvement
        fuel_improvement = calculate_fuel_improvement(dijk_result, ga_result)
        print(f"  Fuel improvement: {fuel_improvement:.1f}%")

        # Store results for CSV export
        results.append({
            "scenario": scenario.name,
            "algorithm": "dijkstra",
            "n_waypoints": len(scenario.waypoints),
            **dijk_result,
            "improvement_pct_vs_dijkstra": 0.0
        })
        results.append({
            "scenario": scenario.name,
            "algorithm": "genetic",
            "n_waypoints": len(scenario.waypoints),
            **ga_result,
            "improvement_pct_vs_dijkstra": fuel_improvement
        })

    # Export to CSV
    export_to_csv(results)
```

### Success Criteria
- [ ] CSV file generated at `ml/routing/benchmarks/results/benchmark_results.csv`
- [ ] CSV contains all required columns including std_dev columns
- [ ] Each scenario has both dijkstra and genetic results
- [ ] Fuel improvement percentages calculated correctly
- [ ] Standard deviation reported for GA results (should be > 0 for stochastic behavior)
- [ ] Manual verification: GA shows 8-20% fuel improvement on average across scenarios

---

## Gap 2: NLP Evaluation Metrics Enhancement

### Objective
Provide comprehensive NLP triage evaluation beyond basic accuracy to support dissertation Chapter 4 requirements:
- Per-category precision, recall, F1 scores
- Confusion matrix for visualization
- Language-specific performance analysis
- Severity-specific accuracy breakdown

### Current State
- <ref_file file="C:\smart-policing-system\ml\nlp\evaluations\evaluate_triage.py" /> calculates only overall accuracy
- Severity breakdown exists but lacks detailed metrics
- No confusion matrix generation
- No per-category precision/recall/F1 calculations

### Implementation Plan

#### Step 1: Add Per-Category Metrics Function
**File**: `ml/nlp/evaluations/evaluate_triage.py`

```python
def calculate_per_category_metrics(test_cases, predictions) -> dict:
    """
    Calculates precision, recall, F1 per category.
    Required for dissertation Table 4.2.
    
    Precision: Of all reports classified as "robbery", what % were actually robbery?
    Recall: Of all actual robberies, what % did we correctly classify?
    F1: Harmonic mean of precision and recall.
    """
    categories = set(c["expected_category"] for c in test_cases)
    metrics = {}
    
    for cat in categories:
        true_positives = sum(
            1 for i, c in enumerate(test_cases)
            if c["expected_category"] == cat and predictions[i].category == cat
        )
        false_positives = sum(
            1 for i, c in enumerate(test_cases)
            if c["expected_category"] != cat and predictions[i].category == cat
        )
        false_negatives = sum(
            1 for i, c in enumerate(test_cases)
            if c["expected_category"] == cat and predictions[i].category != cat
        )
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics[cat] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": sum(1 for c in test_cases if c["expected_category"] == cat)
        }
    
    return metrics
```

#### Step 2: Add Confusion Matrix Export
**File**: `ml/nlp/evaluations/evaluate_triage.py`

```python
def export_confusion_matrix(test_cases, predictions, categories, output_path=None):
    """
    Creates confusion matrix data for dissertation Figure 4.1.
    Row = actual category, Column = predicted category.
    """
    from sklearn.metrics import confusion_matrix
    
    y_true = [c["expected_category"] for c in test_cases]
    y_pred = [p.category for p in predictions]
    
    cm = confusion_matrix(y_true, y_pred, labels=sorted(categories))
    
    result = {
        "matrix": cm.tolist(),
        "labels": sorted(categories)
    }
    
    if output_path:
        import json
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    return result
```

#### Step 3: Integrate into Main Evaluation Loop
**File**: `ml/nlp/evaluations/evaluate_triage.py`

Update `run_evaluation()` to call new functions:

```python
# After existing evaluation loop
category_metrics = calculate_per_category_metrics(entries, results)
confusion_data = export_confusion_matrix(
    entries, 
    results, 
    set(c["expected_category"] for c in entries),
    output_path="ml/nlp/evaluations/results/confusion_matrix.json"
)

# Add to summary output
summary["by_category"] = category_metrics
summary["confusion_matrix"] = confusion_data
```

#### Step 4: Update Summary Output Structure
**File**: `ml/nlp/evaluations/evaluate_triage.py`

Enhance the JSON output to include new metrics:

```python
summary = {
    "total": total,
    "severity_accuracy_pct": round(sev_accuracy, 2),
    "category_accuracy_pct": round(cat_accuracy, 2),
    "language_accuracy_pct": round(lang_accuracy, 2),
    "severity_breakdown": {...},
    "language_breakdown": {...},
    "by_category": category_metrics,  # NEW
    "confusion_matrix": confusion_data,  # NEW
    "individual_results": results,
}
```

### Success Criteria
- [ ] Evaluation script outputs per-category precision/recall/F1 scores
- [ ] Confusion matrix JSON file generated at `ml/nlp/evaluations/results/confusion_matrix.json`
- [ ] JSON output includes "by_category" section with all categories
- [ ] Confusion matrix can be visualized as heatmap for dissertation Figure 4.1
- [ ] Manual verification: HIGH severity recall ≥ 90% (critical for safety)

---

## Gap 3: DBSCAN Parameter Sensitivity Integration

### Objective
Systematically document DBSCAN parameter selection process for dissertation methodology. This is required for:
- Chapter 3 methodology justification
- Table 4.4: DBSCAN Parameter Sensitivity Analysis
- Demonstrating rigorous hyperparameter tuning

### Current State
- `tune_dbscan_parameters()` function exists in <ref_file file="C:\smart-policing-system\backend\app\services\gis\hotspot_analysis.py" lines="190-212" />
- Function not called during benchmark runs
- Results must be manually captured via Flask shell
- No automated export for dissertation tables

### Implementation Plan

#### Step 1: Create Standalone Parameter Tuning Script
**File**: `ml/gis/parameter_tuning.py`

```python
"""
DBSCAN Parameter Sensitivity Analysis
========================================
Standalone script to run parameter tuning and export results for dissertation.
Run this independently of Flask app for clean results.

Usage:
    python -m ml.gis.parameter_tuning
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app import create_app
from app.services.gis.hotspot_analysis import hotspot_service
import json

def run_parameter_tuning(days_back=90, output_path=None):
    """
    Run DBSCAN parameter sensitivity analysis and export results.
    
    Args:
        days_back: Number of days of incident data to analyze
        output_path: Path to save JSON results (default: ml/gis/results/parameter_tuning.json)
    """
    app = create_app("development")
    
    with app.app_context():
        print("Running DBSCAN parameter sensitivity analysis...")
        print(f"Analyzing incidents from past {days_back} days")
        
        results = hotspot_service.tune_dbscan_parameters(days_back=days_back)
        
        # Add metadata for dissertation
        results["metadata"] = {
            "days_back": days_back,
            "epsilon_values_tested": [0.003, 0.005, 0.008, 0.010, 0.015, 0.020],
            "min_samples": 4,
            "selected_epsilon": 0.008,
            "justification": "Epsilon=0.008 provides balanced cluster density (5-8 clusters typical)"
        }
        
        # Save results
        if output_path is None:
            output_path = PROJECT_ROOT / "ml" / "gis" / "results" / "parameter_tuning.json"
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
        print("\nParameter Sensitivity Results:")
        print("=" * 50)
        for eps, data in results.items():
            if eps != "metadata":
                print(f"Epsilon {eps}: {data['clusters']} clusters, {data['noise_points']} noise points")
        
        return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run DBSCAN parameter sensitivity analysis")
    parser.add_argument("--days", type=int, default=90, help="Days of incident data to analyze")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()
    
    run_parameter_tuning(days_back=args.days, output_path=args.output)
```

#### Step 2: Integrate into Master Benchmark Script
**File**: `ml/benchmarks/master_benchmark.py` (new file)

```python
"""
Master Benchmark Runner
========================
Runs all dissertation benchmarks in sequence:
1. Routing algorithm comparison
2. NLP triage evaluation
3. DBSCAN parameter sensitivity
4. System performance metrics

This generates all Chapter 4 data in one run.
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def run_routing_benchmarks():
    """Run routing algorithm comparison with statistical averaging."""
    print("\n" + "=" * 60)
    print("Running Routing Algorithm Benchmarks...")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "ml.routing.benchmarks.run_benchmarks"])

def run_nlp_evaluation():
    """Run NLP triage accuracy evaluation."""
    print("\n" + "=" * 60)
    print("Running NLP Triage Evaluation...")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "ml.nlp.evaluations.evaluate_triage", "--output", "ml/nlp/evaluations/results/full_evaluation.json"])

def run_parameter_tuning():
    """Run DBSCAN parameter sensitivity analysis."""
    print("\n" + "=" * 60)
    print("Running DBSCAN Parameter Sensitivity Analysis...")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "ml.gis.parameter_tuning"])

def run_system_performance():
    """Run system performance metrics."""
    print("\n" + "=" * 60)
    print("Running System Performance Metrics...")
    print("=" * 60)
    subprocess.run([sys.executable, "-m", "ml.routing.benchmarks.system_performance"])

def main():
    print("Crime-Watch Dissertation Benchmark Suite")
    print("=" * 60)
    print("This will generate all Chapter 4 data files.")
    
    run_routing_benchmarks()
    run_nlp_evaluation()
    run_parameter_tuning()
    run_system_performance()
    
    print("\n" + "=" * 60)
    print("All benchmarks complete!")
    print("Results available in ml/*/results/ directories")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

### Success Criteria
- [ ] Standalone parameter tuning script works independently
- [ ] Results exported to JSON with dissertation metadata
- [ ] Master benchmark script runs parameter tuning as part of suite
- [ ] Results can be directly copied to dissertation Table 4.4
- [ ] Manual verification: Epsilon=0.008 produces 5-8 clusters on typical data

---

## Gap 4: System Performance Metrics

### Objective
Measure and document API response times for key endpoints to demonstrate system performance characteristics. Required for:
- Dissertation Table 4.6: System Response Time Analysis
- Demonstrating real-time feasibility
- Performance baseline for future work

### Current State
- No performance measurement script exists
- No API response time data collected
- Cannot generate dissertation performance tables

### Implementation Plan

#### Step 1: Create Performance Measurement Script
**File**: `ml/routing/benchmarks/system_performance.py`

```python
"""
System Performance Metrics
==========================
Measures API response times for key endpoints.
Results go in dissertation Table 4.6: System Response Time Analysis.

Usage:
    python -m ml.routing.benchmarks.system_performance
"""
import time
import statistics
import requests
import argparse
from pathlib import Path

BASE_URL = "http://localhost:5000/api/v1"

def measure_endpoint(method, path, token=None, data=None, n=10):
    """
    Measures API response time for an endpoint.
    
    Args:
        method: HTTP method (GET, POST)
        path: API endpoint path
        token: JWT authentication token (if required)
        data: Request body data (for POST)
        n: Number of measurements to take
    
    Returns:
        dict with mean, min, max response times in milliseconds
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    times = []
    errors = 0
    
    for i in range(n):
        try:
            start = time.perf_counter()
            if method == "GET":
                response = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{path}", headers=headers, json=data, timeout=10)
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            if response.status_code < 400:
                times.append(elapsed_ms)
            else:
                errors += 1
        except Exception as e:
            errors += 1
            print(f"  Error on request {i+1}: {e}")
    
    if not times:
        return {
            "endpoint": path,
            "mean_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "std_ms": 0,
            "errors": n,
            "success_rate": 0.0
        }
    
    return {
        "endpoint": path,
        "mean_ms": round(statistics.mean(times), 1),
        "min_ms": round(min(times), 1),
        "max_ms": round(max(times), 1),
        "std_ms": round(statistics.stdev(times) if len(times) > 1 else 0, 1),
        "errors": errors,
        "success_rate": round((n - errors) / n * 100, 1)
    }

def get_auth_token():
    """Get JWT token for authenticated endpoints."""
    try:
        # Try to login with test credentials
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@test.com", "password": "admin123"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except:
        pass
    return None

def run_performance_measurements(n=10, output_path=None):
    """
    Run performance measurements on all key endpoints.
    
    Args:
        n: Number of measurements per endpoint
        output_path: Path to save JSON results
    """
    print("Crime-Watch System Performance Measurement")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Measurements per endpoint: {n}")
    print()
    
    token = get_auth_token()
    if token:
        print("✓ Authentication token obtained")
    else:
        print("✗ No authentication token - measuring public endpoints only")
    
    results = []
    
    # Public endpoints
    print("\nMeasuring public endpoints...")
    endpoints = [
        ("GET", "/health", None, None),
        ("GET", "/incidents/", None, None),
    ]
    
    for method, path, data, auth_required in endpoints:
        if auth_required and not token:
            print(f"  Skipping {path} (no auth token)")
            continue
        
        print(f"  {method} {path}...", end=" ")
        result = measure_endpoint(method, path, token, data, n)
        results.append(result)
        print(f"{result['mean_ms']:.1f}ms mean ({result['success_rate']:.0f}% success)")
    
    # Authenticated endpoints (if token available)
    if token:
        print("\nMeasuring authenticated endpoints...")
        auth_endpoints = [
            ("POST", "/hotspots/analyze", {"days_back": 30}, True),
            ("GET", "/hotspots/", None, True),
            ("GET", "/hotspots/heatmap?min_lng=30.95&min_lat=-17.95&max_lng=31.20&max_lat=-17.70", None, True),
        ]
        
        for method, path, data, auth_required in auth_endpoints:
            print(f"  {method} {path}...", end=" ")
            result = measure_endpoint(method, path, token, data, n)
            results.append(result)
            print(f"{result['mean_ms']:.1f}ms mean ({result['success_rate']:.0f}% success)")
    
    # Patrol endpoints (require hotspots to exist)
    if token:
        print("\nMeasuring patrol endpoints...")
        patrol_endpoints = [
            ("POST", "/patrol/compare", {"hotspot_ids": []}, True),
        ]
        
        for method, path, data, auth_required in patrol_endpoints:
            print(f"  {method} {path}...", end=" ")
            result = measure_endpoint(method, path, token, data, n)
            results.append(result)
            print(f"{result['mean_ms']:.1f}ms mean ({result['success_rate']:.0f}% success)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"{'Endpoint':<40} {'Mean (ms)':<12} {'Min (ms)':<10} {'Max (ms)':<10} {'Success %':<10}")
    print("-" * 82)
    for r in results:
        print(f"{r['endpoint']:<40} {r['mean_ms']:<12.1f} {r['min_ms']:<10.1f} {r['max_ms']:<10.1f} {r['success_rate']:<10.0f}")
    
    # Save results
    if output_path is None:
        output_path = Path(__file__).parent / "results" / "system_performance.json"
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump({
            "metadata": {
                "base_url": BASE_URL,
                "measurements_per_endpoint": n,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure system API performance")
    parser.add_argument("--n", type=int, default=10, help="Measurements per endpoint")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()
    
    run_performance_measurements(n=args.n, output_path=args.output)
```

#### Step 2: Create Results Directory
**File**: `ml/routing/benchmarks/results/.gitkeep` (already exists)

Ensure the results directory exists for storing performance data.

### Success Criteria
- [ ] Performance script runs without errors
- [ ] Measures at least 5 key endpoints
- [ ] Results saved to JSON with metadata
- [ ] Can generate dissertation Table 4.6 from results
- [ ] Manual verification: All endpoints respond within acceptable time (< 2s mean)

---

## Gap 5: Dissertation Data Export Structure

### Objective
Create organized data export functions that generate structured files for each dissertation figure and table. This ensures:
- Reproducible data for dissertation writing
- Easy import into Excel/Google Sheets for visualization
- Version-controlled evaluation results

### Current State
- Benchmark scripts generate basic CSV/JSON
- No structured export for specific dissertation figures
- Data scattered across multiple files
- No master export function

### Implementation Plan

#### Step 1: Create Dissertation Data Export Module
**File**: `ml/dissertation/data_export.py`

```python
"""
Dissertation Data Export Module
===============================
Generates structured data files for each dissertation figure and table.
This ensures reproducibility and easy import into visualization tools.

Usage:
    from ml.dissertation.data_export import export_all_dissertation_data
    export_all_dissertation_data()
"""
import json
import csv
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = PROJECT_ROOT / "ml" / "dissertation" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def export_routing_comparison_table(results: List[Dict], filename="table_4_5_algorithm_comparison.csv"):
    """
    Export routing algorithm comparison data for dissertation Table 4.5.
    
    Format: scenario,algorithm,n_waypoints,mean_distance_km,std_distance_km,
            mean_time_ms,std_time_ms,mean_fuel_litres,std_fuel_litres,improvement_pct_vs_dijkstra
    """
    filepath = EXPORT_DIR / filename
    
    fieldnames = [
        "scenario", "algorithm", "n_waypoints",
        "mean_distance_km", "std_distance_km",
        "mean_time_ms", "std_time_ms",
        "mean_fuel_litres", "std_fuel_litres",
        "improvement_pct_vs_dijkstra"
    ]
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✓ Table 4.5 exported to {filepath}")
    return filepath

def export_time_vs_size_data(results: List[Dict], filename="figure_4_4_time_vs_size.json"):
    """
    Export computation time vs problem size data for dissertation Figure 4.4.
    
    Format: List of {n_waypoints, algorithm, mean_time_ms, std_time_ms}
    """
    filepath = EXPORT_DIR / filename
    
    # Extract unique waypoint counts
    waypoint_counts = sorted(set(r['n_waypoints'] for r in results))
    
    data = []
    for n in waypoint_counts:
        for algo in ['dijkstra', 'genetic']:
            matching = [r for r in results if r['n_waypoints'] == n and r['algorithm'] == algo]
            if matching:
                data.append({
                    'n_waypoints': n,
                    'algorithm': algo,
                    'mean_time_ms': matching[0]['mean_time_ms'],
                    'std_time_ms': matching[0]['std_time_ms']
                })
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Figure 4.4 data exported to {filepath}")
    return filepath

def export_fuel_vs_size_data(results: List[Dict], filename="figure_4_5_fuel_vs_size.json"):
    """
    Export fuel consumption vs problem size data for dissertation Figure 4.5.
    
    Format: List of {n_waypoints, algorithm, mean_fuel_litres, std_fuel_litres}
    """
    filepath = EXPORT_DIR / filename
    
    waypoint_counts = sorted(set(r['n_waypoints'] for r in results))
    
    data = []
    for n in waypoint_counts:
        for algo in ['dijkstra', 'genetic']:
            matching = [r for r in results if r['n_waypoints'] == n and r['algorithm'] == algo]
            if matching:
                data.append({
                    'n_waypoints': n,
                    'algorithm': algo,
                    'mean_fuel_litres': matching[0]['mean_fuel_litres'],
                    'std_fuel_litres': matching[0]['std_fuel_litres']
                })
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Figure 4.5 data exported to {filepath}")
    return filepath

def export_nlp_category_metrics(metrics: Dict, filename="table_4_2_category_metrics.json"):
    """
    Export NLP per-category metrics for dissertation Table 4.2.
    
    Format: {category: {precision, recall, f1, support}}
    """
    filepath = EXPORT_DIR / filename
    
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✓ Table 4.2 exported to {filepath}")
    return filepath

def export_confusion_matrix_data(confusion_data: Dict, filename="figure_4_1_confusion_matrix.json"):
    """
    Export confusion matrix data for dissertation Figure 4.1.
    
    Format: {matrix: [[...]], labels: [...]}
    """
    filepath = EXPORT_DIR / filename
    
    with open(filepath, 'w') as f:
        json.dump(confusion_data, f, indent=2)
    
    print(f"✓ Figure 4.1 data exported to {filepath}")
    return filepath

def export_parameter_sensitivity_data(results: Dict, filename="table_4_4_parameter_sensitivity.json"):
    """
    Export DBSCAN parameter sensitivity data for dissertation Table 4.4.
    
    Format: {epsilon: {clusters, noise_points}, metadata: {...}}
    """
    filepath = EXPORT_DIR / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Table 4.4 exported to {filepath}")
    return filepath

def export_system_performance_data(results: List[Dict], filename="table_4_6_system_performance.json"):
    """
    Export system performance data for dissertation Table 4.6.
    
    Format: [{endpoint, mean_ms, min_ms, max_ms, std_ms, success_rate}]
    """
    filepath = EXPORT_DIR / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Table 4.6 exported to {filepath}")
    return filepath

def export_all_dissertation_data():
    """
    Master function to export all dissertation data files.
    Call this after running all benchmark scripts.
    """
    print("\n" + "=" * 60)
    print("Exporting Dissertation Data Files")
    print("=" * 60)
    
    # Load benchmark results
    try:
        with open(PROJECT_ROOT / "ml" / "routing" / "benchmarks" / "results" / "benchmark_results.csv") as f:
            routing_results = list(csv.DictReader(f))
        export_routing_comparison_table(routing_results)
        export_time_vs_size_data(routing_results)
        export_fuel_vs_size_data(routing_results)
    except FileNotFoundError:
        print("⚠ Routing benchmark results not found - skipping routing exports")
    
    # Load NLP results
    try:
        with open(PROJECT_ROOT / "ml" / "nlp" / "evaluations" / "results" / "full_evaluation.json") as f:
            nlp_results = json.load(f)
        export_nlp_category_metrics(nlp_results.get("by_category", {}))
        if "confusion_matrix" in nlp_results:
            export_confusion_matrix_data(nlp_results["confusion_matrix"])
    except FileNotFoundError:
        print("⚠ NLP evaluation results not found - skipping NLP exports")
    
    # Load parameter tuning results
    try:
        with open(PROJECT_ROOT / "ml" / "gis" / "results" / "parameter_tuning.json") as f:
            param_results = json.load(f)
        export_parameter_sensitivity_data(param_results)
    except FileNotFoundError:
        print("⚠ Parameter tuning results not found - skipping parameter exports")
    
    # Load system performance results
    try:
        with open(PROJECT_ROOT / "ml" / "routing" / "benchmarks" / "results" / "system_performance.json") as f:
            perf_results = json.load(f)
        export_system_performance_data(perf_results.get("results", []))
    except FileNotFoundError:
        print("⚠ System performance results not found - skipping performance exports")
    
    print("\n" + "=" * 60)
    print(f"All dissertation data exported to: {EXPORT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    export_all_dissertation_data()
```

#### Step 2: Integrate into Master Benchmark Script
**File**: `ml/benchmarks/master_benchmark.py`

Add call to export function at the end:

```python
from ml.dissertation.data_export import export_all_dissertation_data

def main():
    # ... existing benchmark runs ...
    
    print("\n" + "=" * 60)
    print("Exporting dissertation data files...")
    print("=" * 60)
    export_all_dissertation_data()
```

### Success Criteria
- [ ] Export module creates structured JSON/CSV files
- [ ] Each dissertation figure/table has corresponding data file
- [ ] Files organized in `ml/dissertation/exports/` directory
- [ ] Data can be directly imported into Excel/Google Sheets
- [ ] Master benchmark script calls export function automatically

---

## Gap 6: NLP Corpus Validation

### Objective
Validate the NLP test corpus to ensure it meets statistical requirements for academic evaluation:
- Balanced category distribution
- Representative language distribution
- Sufficient sample size per category
- No obvious labeling errors

### Current State
- Corpus has 200 entries (meets minimum requirement)
- No validation script exists
- Category distribution not analyzed
- Language balance not verified

### Implementation Plan

#### Step 1: Create Corpus Validation Script
**File**: `ml/nlp/corpus/validate_corpus.py`

```python
"""
NLP Corpus Validation Script
=============================
Validates the labeled test set for statistical requirements.
Checks category distribution, language balance, and labeling consistency.

Usage:
    python -m ml.nlp.corpus.validate_corpus
"""
import json
import sys
from pathlib import Path
from collections import Counter

CORPUS_PATH = Path(__file__).parent / "labeled_test_set.json"

def validate_corpus():
    """
    Validate corpus and report statistics.
    """
    if not CORPUS_PATH.exists():
        print(f"ERROR: Corpus not found at {CORPUS_PATH}")
        sys.exit(1)
    
    with open(CORPUS_PATH, encoding='utf-8') as f:
        data = json.load(f)
    
    print("Crime-Watch NLP Corpus Validation")
    print("=" * 60)
    print(f"Total entries: {len(data)}")
    print()
    
    # Check required fields
    required_fields = ["id", "text", "expected_severity", "expected_category", "language"]
    missing_fields = []
    for i, entry in enumerate(data):
        for field in required_fields:
            if field not in entry:
                missing_fields.append((i, field))
    
    if missing_fields:
        print("⚠ Missing required fields:")
        for idx, field in missing_fields[:10]:  # Show first 10
            print(f"  Entry {idx}: missing '{field}'")
        if len(missing_fields) > 10:
            print(f"  ... and {len(missing_fields) - 10} more")
    else:
        print("✓ All required fields present")
    
    print()
    
    # Severity distribution
    severity_counts = Counter(e["expected_severity"] for e in data)
    print("Severity Distribution:")
    for sev in ["HIGH", "MEDIUM", "LOW"]:
        count = severity_counts.get(sev, 0)
        pct = count / len(data) * 100
        status = "✓" if 20 <= pct <= 50 else "⚠"
        print(f"  {status} {sev:6s}: {count:3d} ({pct:5.1f}%)")
    
    print()
    
    # Category distribution
    category_counts = Counter(e["expected_category"] for e in data)
    print("Category Distribution:")
    for cat, count in category_counts.most_common():
        pct = count / len(data) * 100
        status = "✓" if count >= 10 else "⚠"
        print(f"  {status} {cat:25s}: {count:3d} ({pct:5.1f}%)")
    
    print()
    
    # Language distribution
    lang_counts = Counter(e["language"] for e in data)
    lang_names = {"en": "English", "sn": "Shona", "nd": "Ndebele"}
    print("Language Distribution:")
    for lang in ["en", "sn", "nd"]:
        count = lang_counts.get(lang, 0)
        pct = count / len(data) * 100
        status = "✓" if count >= 30 else "⚠"
        print(f"  {status} {lang_names[lang]:8s} ({lang}): {count:3d} ({pct:5.1f}%)")
    
    print()
    
    # Cross-tabulation: severity by language
    print("Severity by Language:")
    print(f"{'Language':<12} {'HIGH':<8} {'MEDIUM':<8} {'LOW':<8}")
    print("-" * 36)
    for lang in ["en", "sn", "nd"]:
        lang_name = lang_names[lang]
        lang_data = [e for e in data if e["language"] == lang]
        high = sum(1 for e in lang_data if e["expected_severity"] == "HIGH")
        medium = sum(1 for e in lang_data if e["expected_severity"] == "MEDIUM")
        low = sum(1 for e in lang_data if e["expected_severity"] == "LOW")
        print(f"{lang_name:<12} {high:<8} {medium:<8} {low:<8}")
    
    print()
    
    # Validation summary
    issues = []
    
    # Check category balance
    for cat, count in category_counts.items():
        if count < 10:
            issues.append(f"Category '{cat}' has only {count} samples (recommended ≥10)")
    
    # Check language balance
    for lang in ["sn", "nd"]:
        if lang_counts.get(lang, 0) < 30:
            issues.append(f"Language '{lang}' has only {lang_counts.get(lang, 0)} samples (recommended ≥30)")
    
    # Check severity balance
    for sev in ["HIGH", "MEDIUM", "LOW"]:
        pct = severity_counts.get(sev, 0) / len(data) * 100
        if pct < 20 or pct > 50:
            issues.append(f"Severity '{sev}' is {pct:.1f}% of corpus (recommended 20-50%)")
    
    if issues:
        print("⚠ Validation Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Corpus validation passed")
    
    print()
    print("=" * 60)
    
    return len(issues) == 0

if __name__ == "__main__":
    success = validate_corpus()
    sys.exit(0 if success else 1)
```

#### Step 2: Run Validation Before Evaluation
**File**: `ml/nlp/evaluations/evaluate_triage.py`

Add validation check at start of evaluation:

```python
def run_evaluation(...):
    # Validate corpus first
    from ml.nlp.corpus.validate_corpus import validate_corpus
    print("Validating corpus...")
    if not validate_corpus():
        print("WARNING: Corpus validation failed. Results may not be statistically sound.")
        print("Continuing with evaluation anyway...")
    print()
    
    # ... existing evaluation code ...
```

### Success Criteria
- [ ] Validation script runs without errors
- [ ] Reports category, severity, and language distributions
- [ ] Identifies any statistical imbalances
- [ ] Integrated into evaluation workflow
- [ ] Manual verification: Each category has ≥10 samples, each language ≥30 samples

---

## Implementation Priority and Timeline

### Phase 1: Critical Academic Rigor (Week 1)
1. **Gap 1: Routing Benchmark Statistical Analysis** - Highest priority for Chapter 4
2. **Gap 2: NLP Evaluation Metrics Enhancement** - Required for NLP evaluation section

### Phase 2: Systematic Evaluation (Week 2)
3. **Gap 3: DBSCAN Parameter Sensitivity Integration** - Required for methodology section
4. **Gap 4: System Performance Metrics** - Required for performance analysis

### Phase 3: Data Organization (Week 3)
5. **Gap 5: Dissertation Data Export Structure** - Organizes all outputs for dissertation writing
6. **Gap 6: NLP Corpus Validation** - Ensures data quality before evaluation

### Total Estimated Time: 2-3 weeks

---

## Testing and Verification

### Manual Testing Checklist
- [ ] Run `python -m ml.routing.benchmarks.run_benchmarks` and verify CSV output
- [ ] Run `python -m ml.nlp.evaluations.evaluate_triage` and verify JSON output
- [ ] Run `python -m ml.gis.parameter_tuning` and verify parameter sensitivity results
- [ ] Run `python -m ml.routing.benchmarks.system_performance` and verify performance metrics
- [ ] Run `python -m ml.dissertation.data_export` and verify all export files
- [ ] Run `python -m ml.nlp.corpus.validate_corpus` and verify corpus quality

### Automated Testing
Add pytest tests for each new module to ensure:
- Statistical calculations are correct
- CSV/JSON formats match specifications
- Error handling works properly
- Integration points function correctly

---

## Success Metrics

### Dissertation Readiness
- [ ] All Chapter 4 tables can be generated from exported data
- [ ] All Chapter 4 figures can be created from exported data
- [ ] Statistical validity demonstrated (mean ± std_dev reported)
- [ ] Methodology fully documented (parameter tuning, evaluation approach)

### Academic Standards
- [ ] Results are reproducible (fixed seeds, documented parameters)
- [ ] Evaluation is rigorous (multiple runs, confidence intervals)
- [ ] Data quality is validated (corpus checks, statistical balance)
- [ ] Performance is characterized (response times, scalability)

---

## Notes and Considerations

### Academic Integrity
- All benchmark scripts must use fixed random seeds for reproducibility
- Document any assumptions or limitations in the dissertation
- Report both positive and negative findings honestly
- Acknowledge external dependencies (Gemini API, libraries)

### Future Work
- Consider adding cross-validation for NLP evaluation
- Add scalability testing for larger datasets
- Implement automated report generation
- Add visualization generation directly from data

### Documentation
- Update AGENTS.md with new benchmark commands
- Add this implementation plan to repository documentation
- Document any deviations from the plan during implementation
- Keep dissertation objectives aligned with implementation

---

## Conclusion

This implementation plan addresses all identified gaps between the current Crime-Watch system and dissertation evaluation requirements. By following this plan systematically, the system will be able to:

1. Generate statistically valid algorithm comparison data
2. Provide comprehensive NLP evaluation metrics
3. Document parameter selection methodology
4. Characterize system performance
5. Organize all outputs for dissertation writing
6. Ensure data quality through validation

The modular approach allows for incremental implementation and testing, with clear success criteria for each gap. Completing these enhancements will make the system fully compliant with dissertation academic standards.
