# Road Network Routing System

This directory contains the road network routing infrastructure for the Crime-Watch smart policing system.

## Overview

The routing system provides actual road-network-based pathfinding for patrol route optimization, replacing straight-line distance calculations with real street network distances.

## Architecture

### Components

1. **Graph Storage** (`backend/app/services/routing/graph_store.py`)
   - Loads and manages the immutable road network graph
   - Thread-safe singleton pattern for Flask workers
   - Handles graph lifecycle (not_loaded, loading, ready, failed)

2. **Spatial Index** (`backend/app/services/routing/spatial_index.py`)
   - Efficient nearest-node lookup using UTM projection
   - cKDTree for fast spatial queries
   - Accurate distance calculations in metres

3. **Algorithms** (`backend/app/services/routing/algorithms/`)
   - `dijkstra.py`: Manual Dijkstra implementation using heapq
   - `genetic_algorithm.py`: Manual GA for multi-stop optimization
   - No external routing libraries in primary dissertation path

4. **Route Service** (`backend/app/services/routing/route_service.py`)
   - Input validation and sanitization
   - Point snapping to road network
   - Pairwise path computation
   - Geometry stitching for GeoJSON output

5. **Preprocessor** (`backend/app/services/routing/preprocessor.py`)
   - One-off script for OSM graph extraction
   - Creates Harare-specific road network
   - Outputs compressed graph artifacts

## Data Files

### Graph Artifact (`data/harare_drive_graph.json.gz`)
Compressed JSON file containing:
- **Nodes**: `{node_id: {lat, lng}}`
- **Edges**: `{node_id: [{v, key, length_m, geometry_latlng, highway, name, maxspeed, oneway}]}`

### Metadata (`data/harare_drive_graph_metadata.json`)
Contains:
- Graph version and preprocessing date
- OSM source information
- Node/edge counts
- Geographic bounds
- Performance metrics

## Usage

### Preprocessing (One-time Setup)

```bash
cd backend
python -m app.services.routing.preprocessor
```

This will:
1. Download OSM data for Harare
2. Extract drivable road network
3. Filter to largest weakly connected component
4. Serialize to compressed JSON format

### API Endpoints

#### GET `/api/v1/patrol/status`
Get graph loading status (requires authentication).

```json
{
  "state": "ready",
  "city": "harare",
  "nodes": 15000,
  "directed_edges": 45000,
  "artifact_version": "20240115_120000",
  "memory_bytes": 52428800
}
```

#### POST `/api/v1/patrol/routes`
Generate point-to-point route (requires officer/admin authentication).

**Request:**
```json
{
  "city": "harare",
  "start": {"lat": -17.8292, "lng": 31.0522},
  "end": {"lat": -17.8252, "lng": 31.0475},
  "algorithm": "dijkstra"
}
```

**Response:**
```json
{
  "algorithm": "dijkstra",
  "total_distance_m": 1250.5,
  "nodes_visited": 45,
  "execution_time_ms": 15.2,
  "start_snap_distance_m": 12.3,
  "end_snap_distance_m": 8.7,
  "geometry": {
    "type": "LineString",
    "coordinates": [[31.0522, -17.8292], [31.0475, -17.8252]]
  }
}
```

#### POST `/api/v1/patrol/compare`
Compare baseline vs GA optimization (supports both hotspot and road network modes).

**Road Network Request:**
```json
{
  "city": "harare",
  "start": {"lat": -17.8292, "lng": 31.0522},
  "stops": [
    {"lat": -17.8252, "lng": 31.0475},
    {"lat": -17.8189, "lng": 31.0433},
    {"lat": -17.8216, "lng": 31.0492}
  ],
  "return_to_start": false,
  "seed": 42,
  "ga_config": {
    "population_size": 100,
    "generations": 200,
    "mutation_rate": 0.02,
    "crossover_rate": 0.8
  }
}
```

**Response:**
```json
{
  "comparison": [...],
  "recommendedRouteId": "genetic",
  "routes": [...],
  "road_network_comparison": {
    "baseline": {
      "algorithm": "dijkstra_nearest_neighbour",
      "order": [0, 1, 2, 3],
      "total_distance_m": 5430.2,
      "execution_time_ms": 0,
      "geometry": {...}
    },
    "genetic": {
      "algorithm": "genetic_algorithm",
      "order": [0, 2, 1, 3],
      "total_distance_m": 4890.1,
      "execution_time_ms": 125.4,
      "seed": 42,
      "generations": 200,
      "convergence": [5000, 4950, 4900, 4890.1],
      "geometry": {...}
    },
    "comparison": {
      "distance_saving_pct": 10.0,
      "fuel_proxy_saving_pct": 10.0,
      "fuel_consumption_l_per_km": 0.15
    }
  }
}
```

## Algorithm Details

### Dijkstra Implementation
- Uses `heapq` for priority queue
- Directed graph traversal
- Returns path, distance, nodes visited, execution time
- Handles parallel edges (selects lowest cost)
- Special cases: start_equals_end, no_route

### Genetic Algorithm
- Fixed start point (depot)
- Tournament selection (tournsize=3)
- Ordered Crossover (OX)
- Swap and inversion mutation
- Elitism (preserves best individuals)
- Seeded random for reproducibility
- Convergence tracking for dissertation analysis

### Nearest-Neighbor Baseline
- Deterministic greedy algorithm
- Start point fixed
- Selects nearest unvisited stop at each step
- Tie-breaking by smallest index
- Used as baseline for GA comparison

## Performance Considerations

### Memory Usage
- Graph stored as adjacency list (not matrix)
- Target: < 600 MB for Harare metropolitan area
- Actual usage depends on graph size

### Load Time
- Lazy loading on first request
- Thread-safe initialization
- Single load per Flask worker
- Measured load time stored in metadata

### Snap Distance
- Maximum snap distance: 2 km (configurable)
- UTM projection for accurate distances
- Returns 422 if point too far from network

## Testing

### Unit Tests
```bash
cd backend
pytest tests/unit/test_routing_algorithms.py
pytest tests/unit/test_spatial_index.py
```

### Integration Tests
```bash
pytest tests/integration/test_routing_api.py
```

### Manual Verification
1. Run preprocessor to generate graph
2. Test known routes in Harare CBD
3. Verify distances against independent mapping service
4. Record observations in test documentation

## Dissertation Requirements

### Comparison Naming
- **Baseline**: "Dijkstra pairwise distances + nearest-neighbour ordering"
- **Optimized**: "Dijkstra pairwise distances + GA ordering"
- Not: "Dijkstra vs GA" (this is misleading)

### Performance Metrics
- Record actual measurements (no fabricated targets)
- Track: graph load time, memory usage, route latency
- Document GA convergence data
- Report measured savings (including if < 15%)

### Implementation Constraints
- Manual Dijkstra (no networkx.dijkstra_path)
- Manual GA operators (no DEAP)
- Local computation only (no OSRM/Google)
- Road network distances (no straight-line substitution)

## Troubleshooting

### Graph Not Loading
- Check file permissions on `data/` directory
- Verify graph file exists and is valid
- Check logs for specific error messages
- Use `/api/v1/patrol/status` to check state

### Snap Failures
- Verify coordinates are within Harare bounds
- Check max_snap_distance_m configuration
- Ensure graph is loaded successfully
- Validate input coordinate format

### Performance Issues
- Check graph size (nodes/edges count)
- Monitor memory usage during load
- Profile Dijkstra query performance
- Consider spatial index rebuild if slow

## Future Enhancements

- Add A* as optional validation (with admissible heuristic)
- Support for multiple cities (currently Harare only)
- Real-time traffic integration
- Alternative fuel consumption models
- Multi-objective optimization (distance + risk + time)
