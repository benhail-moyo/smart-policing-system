# Crime-Watch Evaluation & Export Implementation Plan (v2)

> **Supersedes**: the original "Dissertation Gaps Implementation Plan"
> **Purpose**: Produce Chapter 4 evidence that is statistically defensible and matches the objectives, targets and baselines committed to in Chapter 1 / Table 3.5 — not just runnable scripts.
> **Status**: Ready for implementation
> **Owner**: Benhail Moyo

---

## 0. Evaluation Protocol (write this first, code second)

Before any script is written, freeze the following in a single `EVALUATION_PROTOCOL.md` and do not change it mid-run. This is what turns "we ran some benchmarks" into "results are reproducible," which is the honesty principle Chapter 3 already commits to.

- **Baselines** (routing): (1) static/fixed patrol route — the official Chapter 1 comparator for the 15% target, (2) nearest-neighbour ordering, (3) Dijkstra with a fixed visiting order, (4) Google OR-Tools VRP solution on small instances, as an external reference point.
- **Datasets**: frozen snapshots, not live DB queries — `data/snapshots/incidents_YYYYMMDD.geojson`, `data/snapshots/road_network_harare.graphml`, `data/snapshots/nlp_holdout_300.json`. Every benchmark script reads from a snapshot, never from `days_back=N` against a live database.
- **Splits**: NLP corpus split explicitly into dev (≈200, prompt iteration only) and test (300-record holdout, touched exactly once, after the prompt is frozen). Document the freeze date and prompt version.
- **Seeds & runs**: GA — 30 independent seeds per scenario, seed varies, scenario fixed. Compare paired-by-scenario (Wilcoxon signed-rank), not just mean ± std.
- **Coverage constraint**: all routing comparisons must visit the same set of K hotspots. Fuel/time improvements are only valid at equal coverage — otherwise the "winning" route can just skip hotspots.
- **Manifest**: every run writes `run_manifest.json` — git commit hash, library versions, seeds, Gemini model version + date, hardware, snapshot filenames used. This is the single most valuable reproducibility artifact and was missing entirely from v1.

**Success criteria for this section**: `EVALUATION_PROTOCOL.md` exists, is committed to git, and every gap below references it instead of re-deciding baselines/seeds ad hoc.

---

## 1. Data & Corpus Validation (was Gap 6 — now first, not last)

### Objective
Validate the NLP corpus and confirm no data-quality issues before any accuracy number is trusted. Validity comes before evaluation, not after.

### Fixes vs. v1
- Runs **before** Gap 3 (NLP evaluation), not after all other benchmarks.
- Cross-tabulates category × language (12 cells), not just two separate marginal distributions.
- Adds: duplicate/near-duplicate detection, allowed-label enforcement (`Violent` vs `violent` etc.), a train/test leakage check (no synthetic record shares text with the holdout set), and a second-annotator agreement check (Cohen's κ) on ~50 records — Oslea can do this blind pass.
- Explicitly flags author-written reports (a source-of-bias risk: keyword-heavy text you wrote yourself flatters simple classifiers).

### Implementation
`ml/nlp/corpus/validate_corpus.py` — same structure as v1's script, plus:
```python
def check_cross_tab(data):
    """Category x language cell counts — flags any cell < 5."""
    ...

def check_duplicates(data, threshold=0.9):
    """Near-duplicate detection via text similarity (rapidfuzz or TF-IDF cosine)."""
    ...

def check_label_leakage(dev_set, holdout_set):
    """Fails if any holdout text (or near-duplicate) appears in dev/synthetic set."""
    ...

def check_annotator_agreement(sample_path):
    """Cohen's kappa between original labels and second annotator's pass on a subsample."""
    from sklearn.metrics import cohen_kappa_score
    ...
```

### Success Criteria
- [ ] Every category ≥ 10 samples, every language ≥ 30 samples (as v1), **and** every category×language cell ≥ 5
- [ ] Zero leakage between synthetic/dev data and the 300-record holdout
- [ ] Cohen's κ ≥ 0.7 on the annotator-agreement subsample (report the number even if lower — don't hide it)
- [ ] Validation is a hard prerequisite: NLP evaluation script refuses to run against an unvalidated corpus

---

## 2. NLP Triage Evaluation (was Gap 2)

### Objective
Report macro F1 — blended and per-language — against the frozen 300-record holdout, per Table 3.5, with confidence intervals and a real comparator model.

### Fixes vs. v1
- **Macro F1 was never actually computed in v1** — only per-category precision/recall/F1 and overall accuracy. Table 3.5's target is specifically *macro* F1, blended and per-language. Fixed by using `sklearn.metrics.classification_report(output_dict=True)`, which gives macro/weighted F1 directly, instead of hand-rolled category loops.
- Evaluates on the **frozen 300-record holdout only**, with the prompt locked before this run (see §0 splits). The 200-entry corpus stays dev-only.
- **Adds the missing SVM/TF-IDF baseline.** Chapter 3 frames the NLP contribution as "how well does a commercial LLM do at this task" — that claim needs a comparator. Train a simple TF-IDF + linear SVM on the dev set, evaluate on the same holdout, compare with McNemar's test.
- **Adds confidence intervals.** With ~25 records per language/class cell, a language-level F1 can swing widely on n this small. Bootstrap resample (1,000 iterations) to get a 95% CI on each reported F1.
- Temperature fixed to 0 for the Gemini calls; model version and call date logged to the manifest.
- Confusion matrix generation kept from v1 (this part was fine).

### Implementation
`ml/nlp/evaluations/evaluate_triage.py`
```python
from sklearn.metrics import classification_report, confusion_matrix, cohen_kappa_score
import numpy as np

def evaluate_holdout(holdout_path, prompt_version):
    validate_corpus_or_raise(holdout_path)          # Gap 1 dependency — hard fail if unvalidated
    entries = load_holdout(holdout_path)
    predictions = [triage_incident_report(e["text"], temperature=0) for e in entries]

    y_true = [e["expected_category"] for e in entries]
    y_pred = [p["category"] for p in predictions]

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    macro_f1_blended = report["macro avg"]["f1-score"]

    per_language = {}
    for lang in ["en", "sn", "nd"]:
        idx = [i for i, e in enumerate(entries) if e["language"] == lang]
        yt = [y_true[i] for i in idx]
        yp = [y_pred[i] for i in idx]
        per_language[lang] = classification_report(yt, yp, output_dict=True, zero_division=0)["macro avg"]["f1-score"]

    ci = bootstrap_f1_ci(y_true, y_pred, n_boot=1000)

    return {
        "macro_f1_blended": macro_f1_blended,
        "macro_f1_ci95": ci,
        "macro_f1_per_language": per_language,
        "sklearn_report": report,
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "model_version": GEMINI_MODEL_VERSION,
        "prompt_version": prompt_version,
        "eval_date": datetime.utcnow().isoformat(),
    }

def bootstrap_f1_ci(y_true, y_pred, n_boot=1000, alpha=0.05):
    n = len(y_true)
    scores = []
    rng = np.random.default_rng(42)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt = [y_true[i] for i in idx]
        yp = [y_pred[i] for i in idx]
        scores.append(classification_report(yt, yp, output_dict=True, zero_division=0)["macro avg"]["f1-score"])
    lo, hi = np.percentile(scores, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"lower": lo, "upper": hi}

def evaluate_svm_baseline(dev_path, holdout_path):
    """TF-IDF + linear SVM, trained on dev, tested on frozen holdout — comparator for McNemar's test."""
    ...
```

### Success Criteria
- [ ] Macro F1 (blended) reported against the ≥75% target, on the holdout only, with a 95% CI
- [ ] Per-language macro F1 reported separately — any language below target is stated as measured, not hidden in a blended average
- [ ] SVM baseline evaluated on the same holdout; McNemar's test result reported
- [ ] HIGH-severity recall ≥ 90% (safety-critical, carried over from v1)
- [ ] Fallback activation rate and fallback-only accuracy reported (resilience, not failure)

---

## 3. Hotspot Detection — DBSCAN Sensitivity & Predictive Accuracy (was Gap 3)

### Objective
Justify DBSCAN parameters from data (not backwards from a desired cluster count), and — critically — measure the **hit rate and Prediction Accuracy Index (PAI)** that Table 3.5/Objective 2 actually commits to. v1 covered none of this; it only counted clusters and noise points.

### Fixes vs. v1
- Haversine distance is now used throughout (confirmed fixed) — this sweep is only meaningful with that fix in place.
- **Removed the pre-committed answer.** v1 hardcoded `selected_epsilon: 0.008` and a justification string before running anything, with a success criterion of "produces 5–8 clusters." That's circular. Replaced with a k-distance elbow method plus a **temporal holdout**: fit clusters on data up to time T, then measure hit rate/PAI on incidents in [T, T+Δ] that the model never saw.
- MinPts is now swept alongside epsilon (2D sensitivity grid), not fixed at 4.
- If incident data is synthetic/planted, this is explicitly labeled as a **planted-cluster recovery test** (Adjusted Rand Index against ground-truth cluster labels) — a legitimate sanity check, but not evidence of real-world hit rate, and the dissertation must say so.
- Runs against a frozen snapshot file, independent of Flask app context and live DB state — fixes the "not reproducible" issue in v1's `days_back=N`.

### Implementation
`ml/gis/parameter_tuning.py`
```python
def sweep_parameters(snapshot_path, eps_values, minpts_values):
    """2D grid: epsilon x min_samples. No hardcoded 'selected' value — chosen after the sweep."""
    points = load_snapshot(snapshot_path)  # frozen GeoJSON, Haversine-projected
    results = []
    for eps in eps_values:
        for minpts in minpts_values:
            labels = dbscan_haversine(points, eps_m=eps, min_samples=minpts)
            results.append({
                "eps_m": eps, "min_samples": minpts,
                "n_clusters": n_clusters(labels), "n_noise": n_noise(labels),
                "silhouette": silhouette_if_valid(points, labels),
            })
    return results

def elbow_epsilon(points, k):
    """k-distance elbow — data-driven epsilon candidate, computed not asserted."""
    ...

def evaluate_hit_rate_pai(train_snapshot, test_window_snapshot, eps_m, min_samples):
    """
    Fit on train_snapshot; predict hotspot polygons; check what fraction of
    test_window incidents fall inside predicted hotspots (hit rate) and
    compute PAI = (hit_rate) / (area_fraction_covered).
    This is the actual Objective-2 metric — absent from v1 entirely.
    """
    ...

def planted_cluster_recovery(points_with_ground_truth_labels, eps_m, min_samples):
    """ARI against known synthetic cluster assignments — label this as a sanity check only."""
    from sklearn.metrics import adjusted_rand_score
    ...
```

### Success Criteria
- [ ] Epsilon chosen via k-distance elbow + temporal-holdout hit rate, not asserted in advance
- [ ] Hit rate ≥ 70% and PAI reported on the temporal holdout (Objective 2's actual target)
- [ ] 2D sensitivity table (epsilon × MinPts) exported for Table 4.4
- [ ] If using synthetic data: ARI recovery score reported and explicitly labeled as a sanity check, not real-world validation

---

## 4. Patrol Routing Benchmark (was Gap 1)

### Objective
Demonstrate ≥15% fuel and response-time reduction **against the static patrol baseline** (Table 3.5's actual comparator), with statistically sound, paired comparisons, at equal hotspot coverage.

### Fixes vs. v1
- **Baseline corrected.** v1 compared GA against plain Dijkstra — not what Chapter 1 promised. Now benchmarks against: static route, nearest-neighbour, fixed-order Dijkstra, and OR-Tools (external reference, not a claimed contribution).
- **Fixed a real bug**: `calculate_fuel_improvement()` was called with the *averaged* result dict (`mean_fuel_litres`) but read `.estimated_fuel_litres`, an attribute that doesn't exist on that dict — would raise `AttributeError` at runtime.
- **Fuel model de-trivialised.** v1's example numbers were consistent with fuel = distance × constant, making "fuel improvement" redundant with "distance improvement." Fuel is now a function of speed, road class and stop-start behaviour, with the consumption model cited.
- **Coverage-controlled comparison.** All algorithms must visit the same K hotspots; fuel/time deltas are only reported at equal coverage, closing the "win by skipping hotspots" loophole.
- **Statistics fixed.** 30 seeds (not 5) for the GA, Dijkstra/static reported once (deterministic — a std of 0 across 5 runs told us nothing). Paired Wilcoxon signed-rank test per scenario, not just mean ± std.
- **Response time is now actually simulated** — this was the single biggest missing piece in v1, despite being an explicit Table 3.5 metric (ARTR). A discrete-event simulation places patrol vehicles along each candidate route and measures time-to-arrival for a sample of held-out incidents.
- Hotspot Coverage Ratio (HCR) computed and reported alongside fuel/time, not dropped.

### Implementation
`ml/routing/benchmarks/run_benchmarks.py`
```python
N_SEEDS = 30  # was 5 — insufficient for a meaningful std/CI

def run_ga_with_seeds(scenario, n_seeds=N_SEEDS):
    results = [run_genetic_benchmark(scenario, seed=s) for s in range(n_seeds)]
    return results  # keep raw list for paired testing, not just mean/std

def calculate_improvement(baseline_result, candidate_result, metric="fuel_litres"):
    """Fixed: operates on raw per-run result objects, not pre-averaged dicts."""
    base = getattr(baseline_result, f"estimated_{metric}") if metric == "fuel_litres" else getattr(baseline_result, metric)
    cand = getattr(candidate_result, f"estimated_{metric}") if metric == "fuel_litres" else getattr(candidate_result, metric)
    return (base - cand) / base * 100 if base else 0.0

def paired_significance_test(baseline_runs, ga_runs, metric_fn):
    from scipy.stats import wilcoxon
    baseline_vals = [metric_fn(r) for r in baseline_runs]
    ga_vals = [metric_fn(r) for r in ga_runs]
    stat, p = wilcoxon(baseline_vals, ga_vals)
    return {"statistic": stat, "p_value": p}

def simulate_response_times(route, held_out_incidents, vehicle_speed_kmh=40):
    """
    Places a patrol vehicle along `route` over simulated time; for each held-out
    incident, computes elapsed time from vehicle position to incident location
    at the time it occurs. This directly produces ARTR — absent from v1.
    """
    ...

def compute_hcr(route, hotspot_nodes):
    """Fraction of hotspot nodes actually traversed by the route."""
    visited = set(route.node_sequence)
    return len(visited & set(hotspot_nodes)) / len(hotspot_nodes)

def run_or_tools_reference(scenario):
    """External reference solution — not claimed as a dissertation contribution,
    used only to show the hand-implemented GA is within a reasonable margin."""
    from ortools.constraint_solver import routing_enums_pb2, pywrapcp
    ...
```

### Success Criteria
- [ ] Fuel & response-time improvement reported against the **static baseline** specifically, matching Table 3.5's wording
- [ ] All comparisons at equal hotspot coverage (HCR reported per route)
- [ ] Wilcoxon signed-rank p-value reported per scenario, alongside mean ± std over 30 GA seeds
- [ ] Response-time simulation (ARTR) implemented and reported — was entirely missing in v1
- [ ] OR-Tools reference solution reported as a sanity bound, clearly labeled as external/not a contribution
- [ ] Fuel model documented and cited, not a constant multiple of distance

---

## 5. System Performance (was Gap 4)

### Objective
Characterise API latency and throughput under realistic concurrent load, including the full triage pipeline, per Objective 5 / Table (response times, DB response, throughput under stress).

### Fixes vs. v1
- **Removes hardcoded test credentials** (`admin@test.com` / `admin123`) — same anti-pattern already flagged and removed elsewhere in the system. Uses environment-variable-based test auth.
- **Fixes silent failure reporting.** v1's `measure_endpoint` returned `mean_ms: 0` for a fully-failing endpoint, which reads as "instant" in a results table. Failed endpoints now report `None`/excluded, with error counts surfaced explicitly.
- **Fixes state mutation during measurement.** `POST /hotspots/analyze` was called repeatedly inside the same measurement loop, mutating the very data being measured against. Read-heavy and write endpoints are now measured separately, with state reset between write-endpoint runs.
- **Adds concurrency.** Sequential requests measure latency only, not throughput. Adds a Locust load-test script for p50/p95/p99 under concurrent load, run against a production-style server (gunicorn/waitress), not Flask's dev server.
- **Adds the triage pipeline end-to-end** — report submission → Gemini triage → hotspot update → route suggestion — the slowest and most important path, entirely absent from v1's endpoint list.

### Implementation
`ml/performance/locustfile.py`
```python
from locust import HttpUser, task, between

class CommanderUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.token = get_test_auth_token()  # from env, not hardcoded

    @task(3)
    def view_hotspots(self):
        self.client.get("/api/v1/hotspots/", headers=self.auth_headers())

    @task(1)
    def submit_and_triage_report(self):
        # full pipeline: ingestion -> Gemini triage -> hotspot recompute
        self.client.post("/api/v1/incidents/", json=sample_report(), headers=self.auth_headers())

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
```
Run: `locust -f ml/performance/locustfile.py --headless -u 20 -r 2 -t 5m --host http://localhost:5000`

`ml/performance/measure_sequential.py` keeps a lightweight sequential script (v1's original approach, fixed) for endpoints Locust doesn't cover well (single-shot admin operations).

### Success Criteria
- [ ] p50/p95/p99 latency reported under at least 20 concurrent simulated users
- [ ] Full triage pipeline (ingestion → Gemini → hotspot → route) latency measured end-to-end
- [ ] Failed requests reported as failures, never as 0ms
- [ ] No test run mutates state that a later measurement in the same run depends on
- [ ] Test credentials sourced from environment, not hardcoded in the repo

---

## 6. Data Export & Reporting (was Gap 5 — now doubles as the product export feature)

### Objective
Produce both (a) dissertation figures/tables from benchmark output and (b) real system exports (incident reports, executive summaries, patrol briefings as PDF/Excel) using the same template infrastructure — discussed separately as a Crime-Watch product feature.

### Fixes vs. v1
- **Replaces the brittle CSV/JSON re-export layer.** v1's `export_time_vs_size_data()` etc. had real bugs: CSV values load as strings so `sorted(set(r['n_waypoints']))` sorts lexically ('10' before '5'), and `matching[0]` silently drops data when multiple scenarios share a waypoint count. Each benchmark script now writes tidy, typed CSV directly (correct dtypes on write), and a single plotting script (matplotlib) generates figures from that — no intermediate re-shaping layer to get wrong.
- **Fixes the path bug**: v1's `master_benchmark.py` computed `PROJECT_ROOT = Path(__file__).resolve().parents[1]`, which resolves to `ml/`, not the repo root — breaks every downstream path. Fixed to `parents[2]`.
- **Fixes silent failure**: `subprocess.run(...)` without `check=True` let a failing benchmark step print "All benchmarks complete!" regardless. Now uses `check=True` and aborts the suite on failure, with a clear message pointing at the failing stage.
- **Adds the manifest** (see §0) to every export bundle — commit hash, seeds, model versions, snapshot filenames.
- **Reuses the same template layer for product exports.** The WeasyPrint/Jinja2 PDF pipeline built for incident reports and executive summaries (discussed separately) is the same engine that renders Chapter 4 tables/figures — one templating system instead of two.

### Implementation
```
ml/dissertation/
    exports/                  # output directory, gitignored except .gitkeep
    export_figures.py         # matplotlib: reads tidy CSV -> PNG/SVG for each figure
    export_tables.py          # reads tidy CSV/JSON -> formatted CSV/Excel per table
    run_manifest.py           # writes commit hash, versions, seeds, snapshots to json

backend/app/services/export/  # product feature, shared templates with above where useful
    templates/
    pdf_export.py
    excel_export.py
    map_snapshot.py
```

```python
# ml/dissertation/export_figures.py
import pandas as pd
import matplotlib.pyplot as plt

def figure_time_vs_size(csv_path, out_path):
    df = pd.read_csv(csv_path, dtype={"n_waypoints": int})  # typed on read — fixes v1's string-sort bug
    fig, ax = plt.subplots()
    for algo, group in df.groupby("algorithm"):
        group = group.sort_values("n_waypoints")
        ax.errorbar(group["n_waypoints"], group["mean_time_ms"], yerr=group["std_time_ms"], label=algo, marker="o")
    ax.set_xlabel("Number of waypoints")
    ax.set_ylabel("Computation time (ms)")
    ax.legend()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
```

```python
# ml/benchmarks/master_benchmark.py  (path bug fixed)
PROJECT_ROOT = Path(__file__).resolve().parents[2]   # was parents[1] — pointed at ml/, not repo root

def run_stage(name, module):
    print(f"Running {name}...")
    result = subprocess.run([sys.executable, "-m", module], check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Stage '{name}' failed (exit {result.returncode}) — aborting suite")
```

### Success Criteria
- [ ] Each figure/table generated from typed, tidy source data — no string-sort or `matching[0]` bugs
- [ ] `master_benchmark.py` aborts loudly on any stage failure, never prints false success
- [ ] Every export bundle includes `run_manifest.json`
- [ ] Product-facing PDF/Excel export (incidents, hotspots, executive summary) uses the same WeasyPrint/Jinja2 template layer as the dissertation figure/table export

---

## Revised Priority & Timeline

| Phase | Content | Duration |
|---|---|---|
| 0 | Evaluation protocol frozen, snapshots taken, baselines/seeds/splits documented | 2–3 days |
| 1 | Corpus validation (§1) — hard prerequisite for §2 | 2–3 days |
| 2 | NLP evaluation with macro F1, CI, SVM baseline (§2) | 3–4 days |
| 3 | DBSCAN sensitivity + hit rate/PAI on temporal holdout (§3) | 3–4 days |
| 4 | Routing benchmark: correct baseline, coverage control, response-time sim, paired stats (§4) | 5–7 days |
| 5 | Locust load testing + full pipeline latency (§5) | 2–3 days |
| 6 | Figure/table export + manifest, product export feature (§6) | 3–4 days |
| — | SUS questionnaire recruitment (run in parallel with all above — start immediately) | ongoing |

**Total: ~4 weeks**, not the original 2–3 — the response-time simulation and SUS recruitment are the realistic long poles, and were underestimated in v1.

---

## What Changed, At a Glance

| Area | v1 problem | v2 fix |
|---|---|---|
| Routing baseline | Compared GA vs. Dijkstra (not the committed baseline) | Static baseline is the official comparator; NN, fixed-Dijkstra, OR-Tools as secondary |
| Routing bug | `calculate_fuel_improvement` read a nonexistent attribute on an averaged dict | Operates on raw per-run objects |
| Routing stats | n=5 seeds, unpaired mean±std | n=30 seeds, Wilcoxon paired test |
| Response time (ARTR) | Not measured at all | Discrete-event simulation added |
| NLP metric | Per-category F1, no macro F1 | `sklearn.classification_report` — macro F1 blended + per-language |
| NLP data split | Same 200-corpus risk of dev/test overlap | Explicit dev/holdout freeze, evaluated once |
| NLP comparator | None | TF-IDF+SVM baseline, McNemar's test |
| DBSCAN parameter choice | Hardcoded epsilon, justified after the fact | k-distance elbow + temporal-holdout hit rate/PAI |
| DBSCAN metric (Objective 2) | Cluster/noise counts only | Hit rate ≥70%, PAI computed |
| Performance test | Hardcoded creds, mutating state, sequential only, silent 0ms failures | Env-based auth, isolated state, Locust concurrency, explicit failure reporting |
| Export/reshape layer | String-sort bug, silent data drop, wrong `PROJECT_ROOT`, swallowed subprocess failures | Typed tidy CSV, `check=True`, path fixed |
| Reproducibility | None | `run_manifest.json` on every run: commit, seeds, versions, snapshots |
| Data validity | Corpus validation run last | Runs first, hard prerequisite, includes leakage/duplicate/agreement checks |
