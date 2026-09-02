# Hotspot Trend Tracking Implementation Documentation

## Overview
This document describes the implementation of persistent hotspot identity and trend tracking for the Smart Policing System. The system addresses the "flickering" effect where hotspots would disappear and reappear abruptly by implementing a status lifecycle with hysteresis and comprehensive history logging.

## Design Parameters

### Matching Algorithm Parameters
- **MATCH_RADIUS_METERS = 500**: Haversine distance threshold for matching new clusters to existing hotspots (in meters)
- **Matching Algorithm**: Greedy nearest-neighbor with mutual best match to prevent one-to-many assignments
- **Candidate Pool**: ALL hotspots regardless of status (including dormant) to enable reactivation

### Status Lifecycle Parameters
- **COOLING_THRESHOLD = 2**: Number of consecutive missed runs before a hotspot becomes dormant
- **ANALYSIS_CADENCE_HOURS = 6**: Production analysis run frequency (every 6 hours via cron: `0 */6 * * *`)
- **Real-world time window**: 2 consecutive missed runs = 12 hours of inactivity before dormancy

### DBSCAN Parameters (Unchanged)
- **DBSCAN_EPSILON = 0.008**: Spatial clustering parameter (degrees)
- **DBSCAN_MIN_SAMPLES = 4**: Minimum samples for cluster formation

## Database Schema

### Hotspot Model
```python
class Hotspot(db.Model):
    hotspot_id = UUID(primary_key)  # Stable identity across runs
    centroid = GEOMETRY(Point, 4326)  # PostGIS point
    convex_hull = GEOMETRY(Polygon, 4326)  # PostGIS polygon
    dominant_category = String
    incident_count = Integer
    risk_score = Float
    status = Enum('emerging', 'active', 'cooling', 'dormant')
    consecutive_misses = Integer(default=0)
    first_detected_at = DateTime
    last_matched_at = DateTime
    updated_at = DateTime
```

### HotspotHistory Model
```python
class HotspotHistory(db.Model):
    history_id = Integer(primary_key)
    hotspot_id = UUID(foreign_key)
    run_timestamp = DateTime
    centroid = GEOMETRY(Point, 4326)
    incident_count = Integer
    risk_score = Float
    volume_score = Float  # Component of risk score
    severity_score = Float  # Component of risk score
    recency_score = Float  # Component of risk score
    status = String
    dominant_category = String
```

## Status Lifecycle

### State Transitions
1. **emerging**: Newly created hotspot
   - → **active** on first successful match

2. **active**: Matched in most recent run, consecutive_misses = 0
   - → **cooling** on first missed run (consecutive_misses = 1)
   - → **dormant** after COOLING_THRESHOLD+1 missed runs

3. **cooling**: Missed 1–COOLING_THRESHOLD consecutive runs
   - → **active** on reactivation (new match within radius)
   - → **dormant** after COOLING_THRESHOLD+1 missed runs

4. **dormant**: Missed > COOLING_THRESHOLD consecutive runs
   - → **active** on reactivation (new cluster within MATCH_RADIUS_METERS)
   - Excluded from main dashboard by default

### Hysteresis Design Rationale
The status lifecycle provides hysteresis to prevent the flickering effect where hotspots would disappear when incidents age out of the analysis window and reappear when new incidents arrive nearby. The cooling state provides a visual indication that a hotspot is fading without removing it entirely, while the dormant state preserves hotspot identity for potential reactivation.

## Matching Algorithm

### Centroid Distance Matching
1. Calculate Haversine distance between each new cluster centroid and all existing hotspot centroids
2. Filter pairs within MATCH_RADIUS_METERS (500m)
3. Sort candidate pairs by distance ascending
4. Apply greedy nearest-neighbor with mutual best match:
   - Iterate through sorted pairs
   - Assign match if neither cluster nor hotspot is already claimed
   - Skip if either is already matched

### Critical Design Decision: Dormant Hotspot Inclusion
The matching algorithm includes ALL hotspots in the candidate pool, regardless of status. This ensures that dormant hotspots can be reactivated when new clusters form within the match radius, preventing the creation of duplicate hotspots near dormant ones.

### Haversine Distance Formula
```python
def _haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = sin²(delta_lat/2) + cos(lat1_rad) * cos(lat2_rad) * sin²(delta_lon/2)
    c = 2 * atan2(√a, √(1-a))
    
    return R * c  # Distance in meters
```

## Risk Score Calculation

### Component Breakdown
The risk score is calculated as a weighted composite of three components:
- **Volume Score**: min(1.0, incident_count / 20.0)
- **Severity Score**: Average severity weight (HIGH=1.0, MEDIUM=0.5, LOW=0.1)
- **Recency Score**: min(1.0, recent_incidents_7days / 5.0)

### Formula
```
RiskScore = 0.4 * Volume + 0.4 * Severity + 0.2 * Recency
```

### Return Value
The function now returns a tuple: `(total_score, volume_score, severity_score, recency_score)` to enable component-level trend analysis in Chapter 4 evaluation.

## History Logging

### Logging Strategy
- One history entry per hotspot per analysis run
- Includes dormant hotspots to show flat/zero periods in trend charts
- Logs all risk score components for component-level analysis
- Preserves centroid snapshots to track geographic drift over time

### Data Retention
History is append-only with no automatic deletion. This provides complete temporal data for dissertation evaluation and retrospective analysis.

## API Endpoints

### Updated Endpoints
- `GET /api/v1/hotspots/` - List hotspots (excludes dormant by default, use `?include_dormant=true` to include)
- `GET /api/v1/hotspots/all` - List all hotspots regardless of status
- `GET /api/v1/hotspots/<id>` - Get single hotspot with summary statistics
- `GET /api/v1/hotspots/<id>/history` - Get full history time series for hotspot

### Backward Compatibility
The main endpoint maintains backward compatibility by excluding dormant hotspots by default, ensuring existing dashboard functionality continues without modification.

## Frontend Implementation

### Navigation
Single "Hotspot Trends" button added to command center dashboard, linking to `/hotspots/trends`. No other dashboard modifications per requirements.

### Trend Pages
1. **Index Page** (`/hotspots/trends`): Table view of all hotspots with filtering by status and category
2. **Detail Page** (`/hotspots/trends/[id]`): Per-hotspot trend visualization with:
   - Risk score over time line chart
   - Incident count over time bar chart
   - Risk component breakdown (volume/severity/recency)
   - Status timeline visualization
   - Summary statistics (days tracked, reactivations, peak risk)

### Chart Library
Recharts chosen for React ecosystem integration and TypeScript support. Zero-cost implementation with no additional dependencies.

## Testing

### Unit Tests
1. **Haversine Distance Accuracy**: Verifies true meter-based calculation vs degree approximation
2. **Dormant Hotspot Reactivation**: Confirms dormant hotspots are included in matching and can be reactivated
3. **Status Lifecycle Transitions**: Tests complete state machine (emerging→active→cooling→dormant→active)
4. **No Hotspot Deletion Regression**: Replays historical runs to verify no hotspot is ever silently deleted

### Integration Testing
Tests verify continuous history trails for each hotspot_id and proper status transitions across multiple analysis runs.

## Deployment Considerations

### Database Migration
Fresh start approach: existing hotspot data is cleared and replaced with new schema. This is appropriate for early development stage and avoids complex migration logic.

### PostGIS Requirements
Implementation requires PostgreSQL with PostGIS extension. Spatial indexing on centroid column provides efficient geographic queries.

### Production Run Cadence
Analysis runs every 6 hours via cron job. This frequency balances responsiveness with computational load, making the 2-run cooling threshold equivalent to 12 hours of real-world inactivity.

## Methodology Documentation

### Chapter 3 Discussion Points
1. **Spatiotemporal Analysis**: Persistent identity + history table + trend charts provide defensible spatiotemporal analysis capability
2. **Parameter Justification**: 
   - 500m match radius based on DBSCAN epsilon (0.008 degrees ≈ 890m at Harare latitude)
   - 12-hour dormancy threshold balances responsiveness with stability
   - 6-hour analysis cadence provides 4 runs per day for adequate temporal resolution
3. **Hysteresis Design**: Status lifecycle prevents flickering while maintaining operational responsiveness
4. **Reactivation vs New Hotspot**: Matching within radius indicates same hotspot reappearing vs new formation

### Chapter 4 Evaluation Material
1. **Trend Charts**: Risk score over time for 2-3 representative hotspots
2. **Component Analysis**: Volume/severity/recency trends to explain risk score changes
3. **Reactivation Events**: Document and analyze reactivation patterns
4. **Status Distribution**: Analysis of hotspot status distribution over time

## Security and Performance

### Security
- JWT authentication required for all hotspot endpoints
- Admin/officer role restriction for trend pages
- No sensitive data in history logs

### Performance
- PostGIS spatial indexing on centroid column
- Efficient greedy matching algorithm (O(n log n) complexity)
- History logging uses bulk inserts for performance
- Frontend charts use on-demand fetching (no real-time polling)

## Future Enhancements

### Potential Improvements
1. Polygon-based matching using IoU (Intersection over Union) for more precise geographic matching
2. Adaptive match radius based on hotspot density
3. Machine learning for risk score weight optimization
4. Real-time WebSocket updates for trend pages
5. Automated alerting for reactivation events

### Known Limitations
1. Fixed match radius may not work well in areas with varying hotspot density
2. Status lifecycle thresholds are heuristic and may require tuning based on operational data
3. History table growth may require archival strategy for long-running deployments