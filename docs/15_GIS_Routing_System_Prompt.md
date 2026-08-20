# Implementation Prompt: Road-Network Patrol Routing (Crime-Watch)

## Purpose and non-negotiable architecture

Implement road-network routing for the existing Crime-Watch monorepo. Leaflet is only responsible for displaying the returned route. It does not create, store, or traverse a road graph. The Flask backend must load a local, preprocessed OpenStreetMap (OSM) directed graph and run all routing locally.

This is an extension of the existing application, not a separate service.

- Backend: Flask app factory. `patrol_bp` is already registered with URL prefix `/api/v1/patrol` in `backend/app/__init__.py`.
- Frontend: Next.js App Router. Existing BFF handlers proxy requests to Flask using `backendApiUrl`; preserve that pattern.
- Current map: `frontend/src/components/CrimeMap` is loaded client-side from `/map` and `/patrol`. Extend its existing Leaflet integration. Do not introduce `react-leaflet` unless it is deliberately added to `frontend/package.json`; it is not currently installed.
- Existing APIs that must continue to work unchanged: `GET /api/v1/patrol/routes`, `POST /api/v1/patrol/optimize`, and `POST /api/v1/patrol/compare`.
- Existing `DijkstraSolver` is a straight-line nearest-neighbour baseline, not Dijkstra. Replace or retire its routing role; do not label it Dijkstra in API results or dissertation output.

## Dissertation constraints

Objective 3 compares a deterministic multi-stop baseline with a Genetic Algorithm (GA). Use implementations written in this repository:

- Implement point-to-point Dijkstra manually with `heapq`; no `networkx.dijkstra_path`, `pgr_dijkstra`, OSRM, or hosted directions API in the primary path.
- Implement GA selection, Ordered Crossover, mutation, and elitism in local code. Do not use DEAP operators in the primary GA implementation.
- Dijkstra is a shortest-path primitive, not a multi-stop route-ordering competitor. The comparison must be named **Dijkstra pairwise distances + nearest-neighbour ordering** versus **Dijkstra pairwise distances + GA ordering**.
- The reported 15% saving is a target, never an acceptance criterion. Report measured results, including results below 15%.

## Scope and data preparation

Scope the initial graph to Harare metropolitan area. A second city may be added only after the single-city implementation and tests pass. Do not load the full Zimbabwe extract into the request process.

Create `backend/app/services/routing/preprocessor.py` as a one-off command/script, outside the request path.

1. Obtain an OSM PBF extract and crop it to an explicit, version-controlled Harare bounding polygon or bounding box. Record OSM source URL/date, crop bounds, and preprocessing date in graph metadata.
2. Parse a drivable network using OSMnx or Pyrosm. Preserve OSM directionality and parallel edges. Do not create reverse edges for one-way roads.
3. Retain the largest **weakly** connected component for the city graph. Keep its edges directed. Do not use the largest strongly connected component because it removes valid destinations such as cul-de-sacs and one-way access roads.
4. Retain nodes: `id`, `lat`, `lng`.
5. Retain directed edges: `u`, `v`, `key`, `length_m`, `geometry_latlng`, `highway`, `name`, `maxspeed`, and `oneway` when available. `geometry_latlng` is an internal list of `[lat, lng]` positions. Edge length is the initial routing weight.
6. Serialize an immutable graph artifact to `backend/ml/routing/data/harare_drive_graph.json.gz` (or an equivalent documented binary format) plus a metadata JSON file. The format must preserve multiple `u -> v` edges.
7. Log and persist node count, directed edge count, weak-component count, extraction bounds, artifact size, and preprocessing duration.

The runtime graph must use an adjacency list, for example `dict[node_id, list[Edge]]`, rather than an adjacency matrix. It must fit well below 600 MB on the stated development hardware. Do not assert a universal 50 MB artifact or 3-second load time before measuring; record actual figures and set project-specific thresholds from those measurements.

## Runtime graph and snapping

Create these modules under `backend/app/services/routing/`:

- `graph_store.py`: load the immutable graph once per Flask worker, expose `get_graph()`, status metadata, and a test-only reset hook.
- `spatial_index.py`: build a read-only nearest-node index when the graph loads.
- `algorithms/dijkstra.py`: manual Dijkstra implementation.
- `algorithms/genetic_algorithm.py`: manual GA multi-stop optimizer.
- `route_service.py`: input validation, snapping, pairwise paths, geometry stitching, and response construction.

Build the spatial index using coordinates appropriate for distance queries: use a projected local CRS with `cKDTree`, or use a Haversine-aware index with radians. A KDTree over raw longitude/latitude degrees is not an accurate distance metric. Return snap distance in metres and reject points farther than a configured limit (for example, 2 km) with a 422 response.

Do not mutate the loaded graph during a request. The graph and index must be safe for concurrent Flask requests. Lazy loading must be protected so only one request performs initialization; other requests either wait or receive a documented `503 graph_loading` response.

## Algorithms and route semantics

### Point-to-point Dijkstra

`dijkstra(graph, start_node, end_node)` must:

- Use `heapq`, edge `length_m`, and directed adjacency lists.
- Return `path_node_ids`, selected edge IDs/keys, `total_distance_m`, `nodes_visited`, and `execution_time_ms`.
- Correctly distinguish `start_equals_end`, `no_route`, and a valid route.
- Select the lowest-cost parallel edge and retain its geometry for reconstruction.

Use A* only as an optional internal validation/performance feature. If used, its Haversine heuristic must be admissible for metre-based road-distance costs; its result must equal Dijkstra's route distance for the same graph and endpoints.

### Multi-stop patrol routing

Define a patrol as an **open** route by default: start at the depot/current location, visit every requested stop exactly once, and finish at the final stop. Add `return_to_start: true` only when explicitly requested. Do not silently compare an open GA route with a closed baseline route.

For three or more stops:

1. Snap all points once and calculate a directed N x N pairwise road-distance/path matrix using the local Dijkstra implementation. Cache matrix entries only within the request unless a bounded, versioned graph cache is added.
2. If any required directed pair has no route, return a 422 response identifying the affected stops; never substitute Haversine distance.
3. Calculate the deterministic baseline by nearest-neighbour ordering over this same Dijkstra matrix, with documented deterministic tie-breaking.
4. Run a manually implemented GA over the same matrix. Keep the start fixed, use tournament selection, OX crossover, swap or inversion mutation, and elitism. Use a seeded random generator supplied in the request or generated and returned in the response for reproducibility.
5. Fitness for the distance-only comparison is total network distance. A risk/response-priority objective may be offered as a separate, explicitly named mode; it must not be compared as though it optimizes the same objective as distance-only nearest neighbour.
6. Stitch the selected Dijkstra edge geometries in traversal order, removing only adjacent duplicate coordinates.

## API contract and authorization

Use `patrol_bp`; do not create a second backend service or blueprint. Require JWT authentication and enforce the project’s existing officer/admin authorization helper on all new route-generation and graph-status endpoints. Preserve public/history behaviour only where the existing application explicitly requires it.

Add these Flask endpoints:

### `GET /api/v1/patrol/status`

Returns no geometry and no graph internals beyond:

```json
{
  "state": "ready",
  "city": "harare",
  "nodes": 0,
  "directed_edges": 0,
  "artifact_version": "...",
  "memory_bytes": 0
}
```

Allowed states: `not_loaded`, `loading`, `ready`, `failed`.

### `POST /api/v1/patrol/routes`

Point-to-point route request:

```json
{
  "city": "harare",
  "start": {"lat": -17.8216, "lng": 31.0492},
  "end": {"lat": -17.8292, "lng": 31.0522},
  "algorithm": "dijkstra"
}
```

Success response:

```json
{
  "algorithm": "dijkstra",
  "total_distance_m": 0,
  "nodes_visited": 0,
  "execution_time_ms": 0,
  "start_snap_distance_m": 0,
  "end_snap_distance_m": 0,
  "geometry": {"type": "LineString", "coordinates": [[31.0492, -17.8216]]}
}
```

`geometry` is valid GeoJSON: every coordinate is `[longitude, latitude]`, never `[lat, lng]`. The endpoint must return 400 for malformed input, 401/403 for authentication/authorization failures, 422 for out-of-scope, distant snap, or no-route inputs, and 503 when the graph is unavailable/loading.

### `POST /api/v1/patrol/compare`

Extend the existing comparison endpoint without breaking its current fields. It accepts `start`, `stops` (minimum three), optional `return_to_start`, `seed`, and GA tuning values bounded by server-side limits. Return the legacy response shape needed by the current patrol page plus a `road_network_comparison` object containing:

- `baseline`: named `dijkstra_nearest_neighbour`, order, network distance, timing, and GeoJSON geometry.
- `genetic`: order, network distance, timing, seed, generation count, convergence values, and GeoJSON geometry.
- `distance_saving_pct`, `fuel_proxy_saving_pct`, and the shared fuel-proxy assumptions.

Do not claim a response-time saving from distance alone. Estimate time only when a documented speed model is used, and describe it as an estimate.

## Next.js BFF and map integration

Keep the BFF as a thin proxy.

1. Update `frontend/src/app/api/patrol/routes/route.ts` to retain its existing `GET` history proxy and add `POST`, forwarding the JSON body and bearer token to Flask `/patrol/routes`.
2. Keep `frontend/src/app/api/patrol/compare/route.ts` as the `POST` proxy to Flask `/patrol/compare`; pass route input unchanged and preserve non-2xx backend errors.
3. Extend `CrimeMap` using its existing Leaflet patterns. Render returned `LineString` GeoJSON with Leaflet/GeoJSON support, and show explicit start, stop, and end markers. Do not add `react-leaflet` merely because Leaflet is installed.
4. Add road-route selection only to officer/admin patrol workflows. The existing `/map` page must continue rendering incidents, hotspots, and saved route history when routing is unavailable.
5. Validate click inputs before requesting: one start and one end for point-to-point; one start and at least three stops for comparison. Show backend validation messages without exposing stack traces.
6. Preserve existing `MapRoute` compatibility. Add a new optional geometry field/type rather than changing or assuming the legacy saved-waypoint format.

## Migration and compatibility

- Do not change or delete persisted `PatrolRoute` records as part of this feature.
- Add schema migrations only if new persisted route geometry or graph metadata is required. Existing route-history reads must work before and after migration.
- Keep `GET /api/v1/patrol/routes` as route history. `POST /api/v1/patrol/routes` is route generation; the shared path is intentional and must have distinct Flask/Next handlers.
- Remove DEAP from runtime dependencies only after its current usage is fully replaced and tests pass. Do not leave a fallback that relabels a non-GA route as GA.

## Tests and acceptance criteria

Add unit, API, and frontend type/build coverage. At minimum:

1. Dijkstra finds the known shortest path in a small directed fixture and observes one-way edges.
2. Dijkstra returns no route for disconnected directed fixture nodes.
3. Snapping returns the correct node and rejects far-away input.
4. Stitched route geometry is continuous and serializes valid GeoJSON `[lng, lat]` coordinates.
5. Nearest-neighbour and GA both use the supplied directed pairwise matrix, visit each required stop exactly once, and honor `return_to_start`.
6. A fixed seed produces the same GA order and convergence data.
7. Flask endpoints cover 200, 400, 401/403, 422, and 503 cases, and existing patrol history/compare integration tests continue to pass.
8. Next.js typecheck and production build pass. Verify that the map still renders when no road graph exists and that a successful route renders on desktop and mobile.
9. Perform a manual Harare CBD-to-suburb road-distance sanity check against an independently viewed map. Record the observation, graph artifact version, and test date; do not use it as a live routing dependency.
10. Measure and record actual graph load duration, process memory impact, route latency, node visits, and GA convergence for the dissertation. Do not fabricate performance targets or savings.

## Explicit exclusions

- No Google, Mapbox, OSRM SaaS, or other request-time routing/geocoding API.
- No full-country graph in the Flask process.
- No `networkx`, pgRouting, DEAP operators, or other black-box route/GA implementation in the primary dissertation path.
- No straight-line distance substituted for an unavailable road path.
- No silent fallback from a failed GA to a baseline while reporting the result as GA.
