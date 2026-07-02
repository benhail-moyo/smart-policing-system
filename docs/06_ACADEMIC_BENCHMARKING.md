# Phase 6: Academic Benchmarking & Evaluation

> **Prerequisite:** Phases 1–5 complete and functional.  
> **Estimated time:** 4–6 hours  
> **This phase is done when:** `run_benchmarks.py` produces a complete CSV, `evaluate_triage.py` produces an accuracy score, and you have the raw data for all Chapter 4 tables and figures.

---

## Context for Claude

This phase generates your dissertation Chapter 4 data. It is standalone — these scripts run outside Flask and produce CSV/JSON files that you import into Excel/Google Sheets to create charts and tables.

The two evaluation targets from your dissertation:
1. **NLP accuracy ≥ 75%** (from Objective 1)
2. **Patrol fuel reduction ≥ 15%** (from Objective 3)

This phase either confirms those targets or doesn't. Both outcomes are fine academically — what matters is that the measurement is rigorous and honest.

---

## What Needs to Be Built in This Phase

### 6.1 Complete the Routing Benchmark Runner

The existing `ml/routing/benchmarks/run_benchmarks.py` needs these additions:

**Multiple runs with averaging (for statistical validity):**
```python
N_RUNS = 5  # Run each scenario 5 times, take average

def run_with_averaging(scenario, algorithm_fn, n_runs=N_RUNS):
    """
    Runs the algorithm N times and returns averaged metrics.
    GA is stochastic — results vary slightly each run even with seed=42
    because scenario waypoints are randomized per run.
    Dijkstra is deterministic — same result every time.
    
    Report: mean ± std_dev in dissertation for GA results.
    """
    distances = []
    times = []
    for i in range(n_runs):
        result = algorithm_fn(scenario)
        distances.append(result.total_distance_km)
        times.append(result.computation_time_ms)
    
    import statistics
    return {
        "mean_distance_km": statistics.mean(distances),
        "std_distance_km": statistics.stdev(distances) if n_runs > 1 else 0,
        "mean_time_ms": statistics.mean(times),
        "std_time_ms": statistics.stdev(times) if n_runs > 1 else 0,
    }
```

**Output CSV format for dissertation Table 4.X:**
```
scenario,algorithm,n_waypoints,mean_distance_km,std_distance_km,mean_time_ms,std_time_ms,mean_fuel_litres,improvement_pct_vs_dijkstra
harare_5_hotspots,dijkstra,5,12.3,0.0,2.1,0.0,1.85,0.0
harare_5_hotspots,genetic,5,10.8,0.4,145.2,8.3,1.62,12.4
harare_10_hotspots,dijkstra,10,...
```

**Fuel reduction calculation:**
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

**Generate all dissertation figures as data files:**
```python
def export_dissertation_data(all_results: list):
    """
    Exports structured data for each dissertation figure/table.
    """
    # Table 4.1: Algorithm comparison summary
    export_comparison_table(all_results)
    
    # Figure 4.X data: computation time vs problem size (n_waypoints)
    export_time_vs_size_data(all_results)
    
    # Figure 4.Y data: fuel consumption vs problem size
    export_fuel_vs_size_data(all_results)
    
    # Figure 4.Z: GA convergence curves (already saved per scenario)
    print("GA convergence data: ml/routing/benchmarks/results/ga_convergence_*.json")
```

### 6.2 Complete the NLP Evaluation Script

The existing `ml/nlp/evaluations/evaluate_triage.py` needs this hardening:

**Per-category precision and recall:**
```python
def calculate_per_category_metrics(test_cases, predictions) -> dict:
    """
    Calculates precision, recall, F1 per category.
    Required for a proper NLP evaluation in Chapter 4.
    
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

**Confusion matrix export:**
```python
def export_confusion_matrix(test_cases, predictions, categories):
    """
    Creates confusion matrix data for dissertation Figure 4.A.
    Row = actual category, Column = predicted category.
    """
    # Use sklearn's built-in
    from sklearn.metrics import confusion_matrix
    y_true = [c["expected_category"] for c in test_cases]
    y_pred = [p.category for p in predictions]
    cm = confusion_matrix(y_true, y_pred, labels=sorted(categories))
    return cm.tolist(), sorted(categories)
```

**Complete evaluation report structure:**
```json
{
  "summary": {
    "total_cases": 200,
    "severity_accuracy": 0.81,
    "category_accuracy": 0.76,
    "overall_accuracy": 0.78,
    "target_met": true
  },
  "by_severity": {
    "HIGH": { "accuracy": 0.89, "support": 60 },
    "MEDIUM": { "accuracy": 0.74, "support": 80 },
    "LOW": { "accuracy": 0.79, "support": 60 }
  },
  "by_category": {
    "robbery": { "precision": 0.88, "recall": 0.85, "f1": 0.86, "support": 30 },
    ...
  },
  "language_breakdown": {
    "en": { "accuracy": 0.84, "support": 120 },
    "sn": { "accuracy": 0.72, "support": 50 },
    "nd": { "accuracy": 0.70, "support": 30 }
  },
  "confusion_matrix": { "data": [[...]], "labels": [...] }
}
```

### 6.3 DBSCAN Parameter Sensitivity Data

Run the parameter tuning from Phase 3 and export results:

```bash
flask shell
>>> from app.services.gis.hotspot_analysis import hotspot_service
>>> import json
>>> results = hotspot_service.tune_dbscan_parameters(days_back=90)
>>> print(json.dumps(results, indent=2))
```

Screenshot or copy this output — it becomes **Table 3.X: DBSCAN Parameter Sensitivity Analysis** in your Chapter 3.

### 6.4 System Performance Metrics

Create `ml/routing/benchmarks/system_performance.py`:

Test API response times under normal load — not a stress test, just verifying reasonable performance:

```python
"""
Measures API response times for key endpoints.
Results go in Chapter 4 as Table 4.X: System Response Time Analysis.
"""
import time
import requests

BASE_URL = "http://localhost:5000/api/v1"

def measure_endpoint(method, path, token, data=None, n=10):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    times = []
    for _ in range(n):
        start = time.perf_counter()
        if method == "GET":
            requests.get(f"{BASE_URL}{path}", headers=headers)
        else:
            requests.post(f"{BASE_URL}{path}", headers=headers, json=data)
        times.append((time.perf_counter() - start) * 1000)
    
    import statistics
    return {
        "endpoint": path,
        "mean_ms": round(statistics.mean(times), 1),
        "min_ms": round(min(times), 1),
        "max_ms": round(max(times), 1),
    }
```

Endpoints to measure: `/incidents/`, `/hotspots/`, `/hotspots/heatmap`, `/patrol/compare`.

---

## Expected Results and What To Do With Them

### Routing Benchmark Results

For 5 hotspots (typical patrol):
- Dijkstra: ~12km, ~2ms computation
- GA: ~10-11km, ~150ms computation
- Fuel improvement: ~8-15% (varies with hotspot distribution)

For 15 hotspots:
- Dijkstra: ~35km, ~8ms
- GA: ~28-32km, ~400ms
- Fuel improvement: ~12-20%

**If GA is NOT 15% better:** This is an honest research finding. Document it and discuss why in Chapter 4: "The results indicate that the GA achieved X% fuel reduction on average, falling short of the 15% target on smaller scenarios but exceeding it on scenarios with 10+ hotspots." Then recommend larger patrol scenarios as the GA's sweet spot in future work.

### NLP Evaluation Results

If overall accuracy is below 75%:
- Check Shona/Ndebele results separately (language-specific failure?)
- Check HIGH severity recall specifically (missing HIGH = dangerous = document explicitly)
- Consider removing ambiguous categories from the corpus and re-running

---

## Dissertation Notes for This Phase

**Chapter 4 structure this phase generates:**

**4.1 Introduction** — brief description of evaluation methodology

**4.2 NLP Triage Evaluation**
- 4.2.1 Test Dataset Description (200 reports, distribution table)
- 4.2.2 Overall Accuracy Results (Table 4.1)
- 4.2.3 Per-Category Analysis (Table 4.2: precision/recall/F1)
- 4.2.4 Language-Specific Performance (Table 4.3)
- 4.2.5 Confusion Matrix (Figure 4.1)

**4.3 GIS Hotspot Analysis Results**
- 4.3.1 DBSCAN Parameter Selection (Table 4.4 from tuning script)
- 4.3.2 Clustering Output on Seed Data (Figure 4.2: map screenshot)
- 4.3.3 Risk Score Distribution

**4.4 Patrol Optimization Results**
- 4.4.1 Benchmark Scenarios Description
- 4.4.2 Algorithm Comparison Table (Table 4.5)
- 4.4.3 GA Convergence Analysis (Figure 4.3: fitness curve)
- 4.4.4 Computation Time vs Problem Size (Figure 4.4)
- 4.4.5 Fuel Reduction Analysis

**4.5 System Performance**
- 4.5.1 API Response Times (Table 4.6)

**4.6 Discussion of Findings**
- Comparison with objectives
- Limitations observed
- Comparison with related work

---

## What You Learn in This Phase

- **Scientific evaluation methodology:** Averaging over multiple runs, reporting standard deviation, separating training and test data — these are the basics of any empirical research.
- **Precision/recall tradeoffs:** In law enforcement, recall for HIGH severity is more important than precision. Missing a genuine HIGH severity report (false negative) is worse than over-flagging a LOW severity report. This is a real domain-specific insight to discuss in your dissertation.
- **Honest reporting:** If your results don't meet targets, report them honestly. Examiners respect intellectual honesty. They penalize data fabrication far more harshly than underperformance.
