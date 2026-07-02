# Phase 3: GIS Hotspot Analysis

> **Prerequisite:** Phase 2 complete. Incidents can be submitted and classified.  
> **Estimated time:** 5–7 hours  
> **This phase is done when:** Running hotspot analysis on seed data produces ≥1 hotspot polygon and the heatmap endpoint returns a grid of intensity values.

---

## Context for Claude

Building the spatial crime analysis layer for Crime-Watch. This module takes stored `Incident` records with PostGIS coordinates and produces:
1. **Crime hotspots** — polygon boundaries of incident clusters (DBSCAN)
2. **KDE heatmap data** — intensity grid for the Leaflet.js frontend

This is your second core academic contribution. The algorithm choices (DBSCAN + KDE) must be justified and documented. The existing file `backend/app/services/gis/hotspot_analysis.py` has the skeleton — complete it.

---

## What Needs to Be Built in This Phase

### 3.1 Create the Harare Seed Data Script

Before you can test clustering, you need incidents with realistic Harare coordinates. Without this, DBSCAN will find 0 clusters.

**Create `backend/scripts/seed_harare_incidents.py`:**

This script must create 80–100 synthetic incidents clustered in 4–5 realistic Harare crime hotspot zones. Use actual Harare suburb coordinates:

```python
HARARE_HOTSPOT_ZONES = [
    {
        "name": "Mbare",
        "center": (-17.8677, 31.0359),
        "radius_deg": 0.015,
        "incident_types": ["robbery", "assault", "theft"],
        "n_incidents": 22,
    },
    {
        "name": "Highfields",
        "center": (-17.8900, 31.0100),
        "radius_deg": 0.012,
        "incident_types": ["drug_offence", "theft", "vandalism"],
        "n_incidents": 18,
    },
    {
        "name": "Harare CBD",
        "center": (-17.8292, 31.0522),
        "radius_deg": 0.010,
        "incident_types": ["robbery", "fraud", "suspicious_activity"],
        "n_incidents": 25,
    },
    {
        "name": "Budiriro",
        "center": (-17.9100, 31.0200),
        "radius_deg": 0.013,
        "incident_types": ["domestic_dispute", "assault", "theft"],
        "n_incidents": 15,
    },
    {
        "name": "Chitungwiza",
        "center": (-18.0130, 31.0750),
        "radius_deg": 0.018,
        "incident_types": ["robbery", "theft", "drug_offence"],
        "n_incidents": 20,
    },
]
```

For each zone:
- Generate `n_incidents` incidents with coordinates scattered around `center` within `radius_deg` using Gaussian noise
- Assign realistic severities (Mbare/CBD → more HIGH, Budiriro → more MEDIUM)
- Set `status = TRIAGED` and fill in `category`, `severity`, `triage_confidence`
- Use `from_shape(Point(lng, lat), srid=4326)` for the location column

### 3.2 Complete DBSCAN Implementation

The existing `hotspot_analysis.py` has the structure. Fill in and harden these specifics:

**Parameter selection and justification:**

```python
# DBSCAN hyperparameters — document these in your dissertation
DBSCAN_EPSILON = 0.008   # ~800m at Zimbabwe latitude (1 degree ≈ 111km)
                          # Chosen to capture street-level clusters
                          # Too small (0.001) = no clusters
                          # Too large (0.05) = merges distinct suburbs
DBSCAN_MIN_SAMPLES = 4   # Minimum 4 incidents to form a hotspot
                          # Below 3 = noise artifacts
                          # Above 8 = misses emerging hotspots
```

**Add parameter sensitivity analysis method:**
```python
def tune_dbscan_parameters(self, days_back: int = 30) -> dict:
    """
    Tests multiple epsilon values to help select optimal DBSCAN parameters.
    Run this once during development — output goes in dissertation Chapter 3.
    Returns: dict of {epsilon: cluster_count}
    """
    incidents = self._fetch_recent_incidents(days_back)
    coords, _ = self._extract_coordinates(incidents)
    
    results = {}
    for eps in [0.003, 0.005, 0.008, 0.010, 0.015, 0.020]:
        labels = DBSCAN(eps=eps, min_samples=4).fit_predict(coords)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        results[eps] = {"clusters": n_clusters, "noise_points": n_noise}
    
    return results
```

Run this during development and include the output table in your dissertation to justify your epsilon choice.

### 3.3 Risk Score Formula

The existing risk score is a rough estimate. Formalize it:

```python
def _calculate_risk_score(self, incidents: List[Incident]) -> float:
    """
    Composite risk score: 0.0 (no risk) to 1.0 (extreme risk).
    
    Formula components:
    - Volume component (40%): log-normalized incident count
    - Severity component (40%): weighted average of severity levels  
    - Recency component (20%): incidents from last 7 days weighted higher
    
    Document this formula in Chapter 3 as your custom risk metric.
    """
    if not incidents:
        return 0.0
    
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    
    # Volume component
    volume_score = min(1.0, len(incidents) / 20.0)  # Normalized: 20+ incidents = max score
    
    # Severity component
    severity_weights = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.1}
    severity_scores = [
        severity_weights.get(i.severity.value if i.severity else "LOW", 0.1)
        for i in incidents
    ]
    severity_score = sum(severity_scores) / len(severity_scores)
    
    # Recency component
    recent_cutoff = now - timedelta(days=7)
    recent_count = sum(1 for i in incidents if i.created_at >= recent_cutoff)
    recency_score = min(1.0, recent_count / 5.0)  # 5+ recent = max
    
    return round(
        (0.4 * volume_score) + (0.4 * severity_score) + (0.2 * recency_score),
        3
    )
```

### 3.4 Hotspots List Endpoint

Add to `backend/app/api/v1/routes/hotspots.py`:

```python
@hotspots_bp.get("/")
@jwt_required()
def list_hotspots():
    """Returns all current hotspots with centroid coordinates for the map."""
    from geoalchemy2.shape import to_shape
    hotspots = db.session.query(Hotspot).order_by(Hotspot.risk_score.desc()).all()
    
    result = []
    for h in hotspots:
        centroid_coords = None
        if h.centroid:
            pt = to_shape(h.centroid)
            centroid_coords = {"lat": pt.y, "lng": pt.x}
        
        result.append({
            "id": h.id,
            "centroid": centroid_coords,
            "incident_count": h.incident_count,
            "risk_score": h.risk_score,
            "dominant_category": h.dominant_category,
            "analysis_date": h.analysis_date.isoformat(),
        })
    
    return jsonify(result), 200
```

### 3.5 KDE Heatmap Hardening

The existing `generate_kde_heatmap()` returns raw numpy arrays which are not JSON-serializable. Fix this:

```python
def generate_kde_heatmap(self, bbox: Tuple, resolution: int = 50) -> dict:
    # ... existing KDE code ...
    
    # Convert to list of {lat, lng, intensity} objects for Leaflet.heat
    heat_points = []
    for i, lat in enumerate(lat_grid):
        for j, lng in enumerate(lng_grid):
            intensity = float(intensities[i][j])
            if intensity > 0.001:  # Filter near-zero values to reduce payload size
                heat_points.append([float(lat), float(lng), intensity])
    
    # Normalize intensities to 0-1 range
    if heat_points:
        max_intensity = max(p[2] for p in heat_points)
        heat_points = [[p[0], p[1], p[2] / max_intensity] for p in heat_points]
    
    return {"heat_points": heat_points, "count": len(heat_points)}
```

The `heat_points` format `[lat, lng, intensity]` is directly consumable by the Leaflet.heat plugin.

---

## Acceptance Checklist

```bash
# 0. Seed data first
python backend/scripts/seed_harare_incidents.py
# Expected: "Seeded 100 incidents across 5 Harare zones"

# 1. DBSCAN parameter tuning (run once, screenshot output for dissertation)
flask shell
>>> from app.services.gis.hotspot_analysis import hotspot_service
>>> print(hotspot_service.tune_dbscan_parameters())
# Expected: table showing cluster counts at different epsilon values

# 2. Run hotspot analysis
curl -X POST http://localhost:5000/api/v1/hotspots/analyze \
  -H "Authorization: Bearer <officer_token>" \
  -H "Content-Type: application/json" \
  -d '{"days_back": 90}'
# Expected: { "hotspots_generated": 4 } (roughly matching seed zones)

# 3. List hotspots
curl http://localhost:5000/api/v1/hotspots/ \
  -H "Authorization: Bearer <token>"
# Expected: Array of 4-5 hotspot objects with centroids, risk_scores

# 4. Heatmap data
curl "http://localhost:5000/api/v1/hotspots/heatmap?min_lng=30.95&min_lat=-17.95&max_lng=31.20&max_lat=-17.70" \
  -H "Authorization: Bearer <token>"
# Expected: { "heat_points": [[lat, lng, intensity], ...], "count": N }
# heat_points should have several hundred entries

# 5. Community user cannot run analysis
curl -X POST http://localhost:5000/api/v1/hotspots/analyze \
  -H "Authorization: Bearer <community_token>"
# Expected: 403 { "error": "Insufficient permissions" }
```

---

## Dissertation Notes for This Phase

**Chapter 3 — Algorithm Design: DBSCAN**

Document DBSCAN's mechanics:
- Density-based: groups points that are close together, marks outliers as noise
- Two parameters: ε (epsilon: neighborhood radius) and MinPts (minimum points for a core point)
- Advantage over K-Means: does not require pre-specifying number of clusters; handles arbitrary shapes
- Reference: Ester et al., "A density-based algorithm for discovering clusters," KDD 1996

**Chapter 3 — Algorithm Design: KDE**

- Kernel Density Estimation is a non-parametric method for estimating the probability density function of a dataset
- Uses Gaussian kernel with bandwidth selected automatically via Scott's rule (scipy default)
- Output is a continuous intensity surface, more informative than discrete cluster polygons for visualization

**Chapter 3 — Risk Score Formula**

Present your risk score formula as Equation 3.X:

```
RiskScore = 0.4 × VolumeScore + 0.4 × SeverityScore + 0.2 × RecencyScore
```

Justify the weights: Severity and volume are equal primary drivers; recency has lower weight to avoid overreacting to single-day spikes.

**Chapter 4 — Results to present:**
- DBSCAN parameter sensitivity table (epsilon vs clusters found)
- Map screenshot showing hotspot polygons overlaid on Harare
- Risk score distribution chart (what % of hotspots are HIGH risk)

---

## What You Learn in This Phase

- **Coordinate systems:** The difference between WGS84 (EPSG:4326 — lat/lng for storage) and projected systems. In this project we approximate distance in degrees because Harare's urban area is small enough that the error is acceptable. In a national-scale system, you'd project to UTM Zone 36S.
- **DBSCAN:** A genuinely useful algorithm. Unlike K-Means, it works when you don't know how many clusters exist — which is always the case with crime data.
- **Seed scripts:** Professional teams always have seed scripts. "Works on my machine" is not good enough.
- **Composite metrics:** Your risk score is a weighted combination of sub-metrics. This pattern appears everywhere — credit scores, ML feature engineering, business KPIs.
