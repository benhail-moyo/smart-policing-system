# Implementation Prompt: Persistent Hotspot Identity & Trend Tracking (Option A)

## Context for the coding assistant

You are extending the Crime-Watch hotspot analysis engine (`hotspot_analysis.py`, Flask backend, Next.js/React frontend, PostgreSQL/PostGIS). The current implementation runs DBSCAN on a rolling time window and **completely replaces** all hotspot records on every run. This causes hotspots to disappear abruptly once their contributing incidents age out of the window, then reappear from scratch when new incidents arrive nearby — producing a "flickering" effect with no visible cause.

This prompt implements **persistent hotspot identity across runs**, a **status lifecycle with hysteresis** (to stop the flicker), a **history log** for every run, and a **new dedicated frontend page** (not the main dashboard) that visualizes each hotspot's trend over time. The main command dashboard gets exactly one addition: a button/nav link to this new page. Do not add charts, trend widgets, or additional cards to the existing dashboard — all of that belongs on the new page.

Constraints to respect throughout:
- Zero-cost infrastructure. No new paid services, no commercial charting SaaS.
- Existing stack only: Flask (app-factory pattern), PostgreSQL + PostGIS, GeoAlchemy2, Next.js/React, react-leaflet. Use **Chart.js** or **Recharts** for charts (already available per project constraints) — do not introduce a new charting dependency without flagging it first.
- Next.js API routes remain **thin proxies only**. All matching/status logic lives in Flask.
- NetworkX/DBSCAN/etc. usage stays consistent with what's already documented in Chapter 3 — do not silently change the clustering algorithm itself, only what happens to its output across runs.
- Every schema and logic decision must be defensible in a dissertation Methodology chapter — prefer simple, explainable heuristics over "clever" ones.

---

## Phase 1: Database schema

### 1.1 New table: `hotspots` (replaces "complete replacement" table if one exists, or extends it)

Persistent hotspot records. A row here represents one hotspot's **current** state, keyed by a stable ID that survives across analysis runs.

Columns:
- `hotspot_id` (UUID or serial, primary key) — stable identity across runs
- `centroid` (PostGIS `GEOMETRY(Point, 4326)`)
- `convex_hull` (PostGIS `GEOMETRY(Polygon, 4326)`)
- `dominant_category` (text)
- `incident_count` (integer) — count in the current active window
- `risk_score` (float)
- `status` (enum/text: `emerging`, `active`, `cooling`, `dormant`)
- `consecutive_misses` (integer, default 0) — number of consecutive runs where no match was found
- `first_detected_at` (timestamp)
- `last_matched_at` (timestamp) — last run where this hotspot had a live match
- `updated_at` (timestamp)

### 1.2 New table: `hotspot_history`

Append-only log. One row per hotspot per analysis run, regardless of status. This is what powers the trend charts and gives you retroactive Chapter 4 evaluation data even if the live matching logic needs future tuning.

Columns:
- `history_id` (serial, primary key)
- `hotspot_id` (foreign key -> `hotspots.hotspot_id`)
- `run_timestamp` (timestamp)
- `centroid` (PostGIS Point) — snapshot at this run, in case centroid drifts over time
- `incident_count` (integer)
- `risk_score` (float)
- `volume_score`, `severity_score`, `recency_score` (floats) — log the components, not just the composite, so Chapter 4 can show component-level trends if useful
- `status` (text) — status *as of this run*
- `dominant_category` (text)

### 1.3 Migration notes

- Write this as a proper migration (Alembic if already in use for the project; otherwise a versioned SQL script consistent with how the rest of the schema is managed).
- If a prior `hotspots` table already exists from the complete-replacement design, migrate it: existing rows become the seed for `hotspots`, each gets a freshly generated `hotspot_id`, and a single `hotspot_history` row is backfilled for each as the "first known" data point.

---

## Phase 2: Backend — matching, status lifecycle, and run logic

### 2.1 Centroid-distance matching

After DBSCAN produces this run's clusters (with fresh centroids), match them against the current `hotspots` table:

- For each **new** cluster centroid, find the nearest existing hotspot centroid (of any status except fully archived, if you add that later) within a configurable `MATCH_RADIUS_METERS` (default: 500m — same order of magnitude as your DBSCAN ε, document this choice explicitly in Chapter 3 as a design parameter, not a magic number).
- Use Haversine distance for this comparison (same fix as discussed for the DBSCAN metric itself — don't reintroduce the Euclidean-on-degrees bug here).
- Matching should be **greedy nearest-neighbor with mutual best match** to avoid one old hotspot being claimed by two new clusters: sort candidate pairs by distance ascending, assign matches greedily, skip any hotspot or cluster already claimed.
- **Matched pair** → update the existing `hotspots` row (new centroid, incident_count, risk_score, dominant_category, `updated_at`, `last_matched_at` = now, `consecutive_misses` = 0). Advance status per the lifecycle rules below.
- **Unmatched new cluster** → insert a new `hotspots` row with `status = 'emerging'`, `consecutive_misses = 0`.
- **Unmatched existing hotspot** (had no matching cluster this run) → increment `consecutive_misses`, do NOT delete the row, advance status per lifecycle rules below.

### 2.2 Status lifecycle (hysteresis)

This is the core fix for the flicker bug. States and transitions:

- `emerging`: newly created this run (no prior match). On its *next* successful match, transitions to `active`.
- `active`: matched in the most recent run, `consecutive_misses = 0`.
- `cooling`: matched previously but missed 1–2 consecutive runs (`consecutive_misses` in `[1, COOLING_THRESHOLD]`, default `COOLING_THRESHOLD = 2`). Still shown on the main map/dashboard, but visually distinguished (e.g. amber vs. red) so commanders see it's fading, not gone.
- `dormant`: missed more than `COOLING_THRESHOLD` consecutive runs. Excluded from the main dashboard's "active hotspots" view by default, but **not deleted** — remains queryable on the trend page. If a dormant hotspot later gets a new match (new cluster forms near its last known centroid within `MATCH_RADIUS_METERS`), it is **reactivated** (status → `active`, `consecutive_misses` reset) rather than treated as a brand-new hotspot. This reactivation-vs-new-hotspot distinction is worth a sentence in Chapter 3 — it's the difference between "this hotspot came back" and "a new hotspot happened to form nearby," and reactivation is the more defensible read when the match falls within radius.

Make `COOLING_THRESHOLD` and `MATCH_RADIUS_METERS` configuration constants (not hardcoded inline), and log the chosen values in your Chapter 3 write-up as explicit design parameters.

### 2.3 History logging

On every analysis run, after matching/status resolution is complete, write one `hotspot_history` row per hotspot that exists post-run (matched, emerging, cooling, or dormant) — dormant hotspots still get a history row so the trend chart shows the flat/zero period rather than a gap.

### 2.4 API endpoints (Flask)

Add these; keep existing hotspot endpoints backward-compatible where possible:

- `GET /api/hotspots` — existing endpoint, but now filter to `status IN ('emerging', 'active', 'cooling')` by default (dormant excluded) unless a query param `include_dormant=true` is passed. This is what the main dashboard map continues to use — **no changes needed on the dashboard side beyond consuming the existing response shape.**
- `GET /api/hotspots/all` — returns all hotspots regardless of status, for the new trend page's index/list view.
- `GET /api/hotspots/<hotspot_id>/history` — returns the full `hotspot_history` time series for one hotspot (ordered by `run_timestamp`), for the trend page's detail/chart view.
- `GET /api/hotspots/<hotspot_id>` — single hotspot current state + summary stats (first_detected_at, total runs tracked, current streak, etc).

### 2.5 Testing

- Unit test the matching function directly with synthetic centroid sets (known matches, known non-matches, edge case of two old hotspots equidistant from one new cluster).
- Test the full status transition table: emerging→active, active→cooling, cooling→dormant, dormant→active (reactivation), and confirm `consecutive_misses` resets correctly at each transition.
- Regression test: replay a sequence of historical runs (even synthetic ones) and confirm no hotspot is ever silently deleted — every hotspot_id that ever appears in `hotspots` should have a continuous `hotspot_history` trail.

---

## Phase 3: Frontend — dedicated trend page (not the dashboard)

### 3.1 Navigation change (the only dashboard-side change)

On the existing command dashboard, add a single button/nav link: **"Hotspot Trends"** (or similar), routing to a new page, e.g. `/hotspots/trends`. No new widgets, cards, or charts on the dashboard itself.

### 3.2 New route: `/hotspots/trends` — index view

A dedicated page, separate component tree from the dashboard. Contents:

- A list/table of all hotspots (calls `GET /api/hotspots/all`), showing: dominant category, current status (with a clear visual badge — active/cooling/dormant/emerging), current risk score, first detected date, last matched date.
- Sortable/filterable by status and category at minimum.
- Each row links to a detail view: `/hotspots/trends/[hotspot_id]`.

### 3.3 New route: `/hotspots/trends/[hotspot_id]` — detail view

Per-hotspot trend charts, calling `GET /api/hotspots/<id>/history`:

- **Risk score over time** (line chart) — the primary trend visualization.
- **Incident count over time** (line or bar chart).
- **Status timeline** — a simple horizontal strip showing status per run (color-coded segments) so a commander can see at a glance when the hotspot was active vs. cooling vs. dormant, and for how long.
- Optionally, the three risk sub-components (volume/severity/recency) as a stacked or multi-line chart, since you're already logging them — useful for Chapter 4 discussion of *why* a risk score moved, not just that it did.
- Basic summary stats at the top: total days tracked, number of reactivations (if any), peak risk score and when it occurred.

### 3.4 Design notes

- Keep this page visually consistent with the rest of the app (reuse existing component library / Tailwind config) but it can be denser/more data-heavy than the dashboard — it's an analysis page, not an operational one.
- This page is for exploration/analysis (commanders or, more likely, you during evaluation) — it does not need real-time polling. On-demand fetch on page load is fine.

---

## Phase 4: Chapter tie-in (for your own reference, not the coding assistant)

Once built, this gives you:
- A defensible answer to "how is this spatiotemporal?" — persistent identity + history table + trend charts.
- Direct Chapter 4 evaluation material: pick 2–3 real hotspots from your test run and show their risk-score-over-time chart as a figure, discuss a reactivation event if one occurs.
- A fix for the flicker bug that's also a good "problem identified → root cause → design decision → resolution" narrative for your methodology chapter — this kind of iteration is normal and valuable to document, not something to hide.

---

## Explicit out-of-scope for this prompt (flag if the coding assistant starts drifting here)

- No polygon/IoU-based matching — centroid distance only, as decided.
- No real-time push/websocket updates to the trend page — on-demand fetch only.
- No changes to the DBSCAN clustering algorithm itself, only to what happens to its output across runs.
- No new hotspot categories, no changes to the risk score formula (that's a separate, already-flagged discussion about weight justification).
