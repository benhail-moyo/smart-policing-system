# Implementation Prompt: Patrol Route Optimization Module (Crime-Watch)

## Context
This is **not** a standalone app — it is a new capability inside the existing Crime-Watch monorepo:

- **Backend:** Flask, app factory pattern, PostgreSQL/PostGIS, GeoAlchemy2, JWT auth, existing structure at `backend/app/services/routing/`, `backend/app/services/gis/`, `backend/app/api/v1/routes/`
- **Frontend:** Next.js (App Router), TypeScript, existing pages at `frontend/src/app/map/`, `frontend/src/app/patrol/`, existing API route handlers at `frontend/src/app/api/patrol/routes/` and `frontend/src/app/api/patrol/compare/` (these act as a thin BFF layer proxying to Flask — confirm this assumption before building, adjust prompt if the Next.js routes are meant to hold logic directly instead)
- `leaflet` + `@types/leaflet` are already installed in `frontend/node_modules` — use `react-leaflet`, not vanilla Leaflet + HTML

**Dissertation objective this maps to:** Objective 3 (Patrol Optimization Engine, Dijkstra vs Genetic Algorithm, target ≥15% fuel/response-time reduction) and Objective 4 (unified system). Chapter 3 requires the algorithms to be **implemented from scratch**, not called as black-box library functions — `networkx.dijkstra_path`, `pgr_dijkstra`, etc. are for benchmarking/comparison only, never for the primary implementation.

**Scope decision (per Chapter 1 delimitations):** road network graph is scoped to **1–2 metropolitan areas** (recommend Harare, optionally + Bulawayo), not the full Zimbabwe extract. Mention country-wide expansion as future work in Chapter 5, don't build it now.

**Hardware constraints:** local dev machine, Intel i5 (12th gen U-series), 8GB RAM. Preprocessing is a one-off local script — does not need Colab. Backend graph-in-memory footprint must stay well under available RAM (target: under 600MB for the scoped city graph).

**Cost constraint:** $0. No paid routing/geocoding APIs (no Google Maps, Mapbox Directions, OSRM SaaS). All graph computation runs locally in the existing Flask process.

---

## Phase 1: Data Preprocessing (`backend/app/services/routing/preprocessor.py`)

One-off script, run locally, not part of the request/response path.

1. Download the relevant `.osm.pbf` extract for the scoped city/cities (Geofabrik doesn't do city-level extracts for Zimbabwe directly — use a bounding-box extract tool like `osmium extract` against the Zimbabwe country file, or BBBike's city extract service, to cut down to Harare's metro bounding box before parsing).
2. Parse with `osmnx` or `pyrosm`, filtering strictly to `network_type='drive'` (exclude footways, steps, cycleways, unpaved/unclassified tracks unless clearly drivable).
3. Extract the largest strongly connected component to avoid dead-end/disconnected subgraphs.
4. Keep only: **nodes** (`node_id`, `lat`, `lng`), **edges** (`u`, `v`, `length_m`, `geometry` as `[[lat,lng], ...]`).
5. Export to `backend/ml/routing/data/{city}_drive_graph.json` (or `.gpickle`). Target: well under 50MB per city, loads in under 3 seconds.
6. Log basic graph stats (node count, edge count, connectivity check) — you'll want these numbers for Chapter 4.

---

## Phase 2: Spatial Indexing (`backend/app/services/routing/spatial_index.py`)

1. On Flask app startup (or lazily on first request, cached), build a `scipy.spatial.KDTree` over all node coordinates.
2. Expose `get_nearest_node(lat, lng) -> node_id`, snapping an arbitrary click point to the nearest graph node in O(log N).

---

## Phase 3: Core Algorithms (`backend/app/services/routing/algorithms/`) — written from scratch

### `dijkstra.py`
- Implement explicitly with `heapq` as the priority queue. Do not call `networkx.dijkstra_path` or any pre-built shortest-path function.
- **Input:** `graph`, `start_node`, `end_node`
- **Returns:** `path_nodes`, `total_distance_m`, `nodes_visited`, `execution_time_ms`

### `a_star.py`
- Implement with `heapq`, Haversine distance as the admissible heuristic.
- Same input/output shape as Dijkstra, for direct comparison.
- *(Note: your dissertation compares Dijkstra vs Genetic Algorithm, not A* vs Dijkstra — build A* only if you want an extra internal sanity check that your Dijkstra implementation is correct, since A* should match Dijkstra's distance exactly while visiting fewer nodes. Not required for Chapter 4 unless you want to widen the comparison.)*

### `genetic_algorithm.py`
- For multi-stop patrol routes (3+ waypoints — the actual "patrol route" use case, as opposed to point-to-point).
- Workflow:
  1. Build an N×N pairwise distance matrix between stops using the Dijkstra implementation above (not straight-line distance — you want real road distance for a fair fuel comparison).
  2. Population of random stop-order chromosomes.
  3. Tournament selection, Ordered Crossover (OX), swap or inversion mutation.
  4. Fitness = inverse of total tour distance.
  5. Return the ordered stop sequence, stitch the individual Dijkstra path geometries into one continuous route.
- Log generation-by-generation best fitness — you'll want a convergence chart for Chapter 4.

---

## Phase 4: Flask Integration (`backend/app/api/v1/routes/`)

Extend the existing `patrol` routes rather than creating a new blueprint, if one already exists:

- `GET /api/v1/patrol/status` — graph load status (nodes/edges loaded, city scope, memory footprint)
- `POST /api/v1/patrol/routes` — single origin/destination request:
  ```json
  { "start": {"lat": -17.8216, "lng": 31.0492},
    "end": {"lat": -17.8292, "lng": 31.0522},
    "algorithm": "dijkstra" }
  ```
  Response includes `total_distance_km`, `nodes_visited`, `execution_time_ms`, GeoJSON `LineString`.
- `POST /api/v1/patrol/compare` — runs the same request through both Dijkstra and GA (for 3+ stop patrol plans) and returns both results side-by-side. This is your Chapter 4 comparison endpoint — design its response shape around what you'll actually plot (distance, time, fuel-proxy estimate for both).

Keep this consistent with whatever auth/role pattern (JWT, role enforcement) the rest of the API already uses — routing endpoints should probably require `officer` or `admin` role, not be open to `community` users.

---

## Phase 5: Frontend (`frontend/src/app/map/`)

Use `react-leaflet`, not vanilla HTML/JS — it's already the frontend framework in use.

1. Map component centered on the scoped city (e.g. Harare: `-17.8292, 31.0522`, zoom ~12), OpenStreetMap tile layer.
2. Algorithm selector (Dijkstra / Genetic Algorithm for multi-stop).
3. Click handling: first click = origin marker, subsequent clicks = additional stops (GA mode) or destination (single-route mode).
4. On stop placement, call the existing `frontend/src/app/api/patrol/routes` (or `/compare`) handler, which proxies to the Flask endpoint above.
5. Render returned GeoJSON as a `Polyline`/`GeoJSON` layer.
6. Metrics panel: latency, distance, nodes visited (Dijkstra) or generations/convergence (GA).

---

## Verification & Acceptance Tests

1. **Load test:** scoped city graph loads into the Flask process in under 3s, under 600MB RAM.
2. **Correctness:** query Harare CBD → a known suburb, path completes with no broken edges, distance is sane (sanity-check manually against Google Maps distance — you won't cite Google Maps in the dissertation, it's just your own sanity check).
3. **Comparison validity:** for the same multi-stop set, log Dijkstra-sequential-visit distance vs GA-optimized distance — this delta is your headline "≥15% fuel reduction" evidence. If you don't hit 15%, report the real number honestly in Chapter 4 and discuss why, rather than adjusting the target after the fact.
4. **Offline viability:** no external routing/geocoding calls at request time — only the local Flask process and your preprocessed graph file.

---

## What NOT to do
- Don't spin up a second backend service (FastAPI or otherwise) for this — it undermines Objective 4 and doubles your maintenance/demo burden.
- Don't build the full-country graph — scope creep against your own delimitations for no dissertation benefit.
- Don't use `pgr_dijkstra`, `networkx.shortest_path`, or any black-box shortest-path call as your primary implementation — benchmark against them in Chapter 4 if you want, but the graded implementation must be your own code.
