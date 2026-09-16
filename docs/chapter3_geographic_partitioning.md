# Geographic Partitioning for Multi-Vehicle Patrol Routing

## Chapter 3: Methodology

### 3.1 Multi-Vehicle Routing Problem Formulation

The single-vehicle patrol routing problem (Section 2.3) extends naturally to a multi-vehicle scenario where N patrol vehicles must collectively cover all high-risk hotspots in a given geographic area. This problem can be formulated as a Vehicle Routing Problem (VRP) with the following characteristics:

**Objective**: Minimize total patrol distance while ensuring complete hotspot coverage across all vehicles.

**Constraints**:
- Each hotspot must be visited by exactly one vehicle
- Each vehicle starts from a designated depot (police station)
- Vehicles operate independently with no inter-vehicle coordination during patrol
- Total number of vehicles N is predetermined by resource availability

**Decision Variables**:
- Assignment of each hotspot to a specific vehicle
- Ordering of hotspots within each vehicle's route
- Return-to-depot requirement (optional)

### 3.2 Heuristic Decoupling Approach

Rather than solving the full VRP as a joint optimization problem (which is NP-hard and computationally expensive), we employ a **heuristic decoupling approach** that separates the problem into two sequential phases:

1. **Geographic Partitioning Phase**: Assign hotspots to vehicles based on spatial proximity
2. **Route Optimization Phase**: Apply existing single-vehicle algorithms (Dijkstra/Genetic) independently to each partition

This approach trades optimality for computational efficiency, which is appropriate for real-time patrol planning in resource-constrained environments.

**Theoretical Justification**:
- Geographic clustering is a natural heuristic for urban patrol routing
- Police vehicles typically operate in designated geographic zones
- Decoupling reduces computational complexity from O(N!) to O(N × K) where K is the average partition size
- Empirical results (Chapter 4) show acceptable load imbalance for practical N values

### 3.3 Partitioning Algorithms

#### 3.3.1 Single-Depot KMeans Clustering

**Scenario**: All N vehicles start from the same police station (central depot).

**Algorithm**: KMeans++ clustering with N clusters.

**Mathematical Formulation**:
```
Given: H = {h₁, h₂, ..., hₘ} hotspot centroids in ℝ²
Find: Cluster assignments C = {c₁, c₂, ..., cₙ} where cᵢ ⊆ H
Minimize: Σᵢ Σₕ∈cᵢ ||h - μᵢ||²
Where: μᵢ is the centroid of cluster cᵢ
```

**Implementation Details**:
- Uses scikit-learn's KMeans with k-means++ initialization
- Standard parameters: n_init=10, max_iter=300, random_state=42
- Haversine distance for geographic coordinates (converted to radians)
- Fallback to round-robin if KMeans produces degenerate clusters

**Advantages**:
- Natural geographic partitioning
- Proven convergence properties
- Efficient O(m × n × k) complexity where m = hotspots, n = vehicles, k = iterations

**Limitations**:
- May produce load imbalance for unevenly distributed hotspots
- Assumes single depot location
- Sensitive to coordinate system scaling

#### 3.3.2 Multi-Depot Nearest-Depot Assignment

**Scenario**: Vehicles start from different police stations (distributed depots).

**Algorithm**: Nearest-depot assignment using Haversine distance.

**Mathematical Formulation**:
```
Given: H = {h₁, h₂, ..., hₘ} hotspots, D = {d₁, d₂, ..., dₙ} depot locations
Assign: For each hotspot hᵢ, find argminⱼ dist(hᵢ, dⱼ)
Where: dist is Haversine distance on Earth's surface
```

**Implementation Details**:
- Haversine formula for great-circle distance
- Earth radius R = 6,371 km
- Each hotspot assigned to closest depot
- No clustering iteration required (O(m × n) complexity)

**Advantages**:
- Correct for multi-depot scenarios
- Computationally efficient
- Intuitive assignment based on proximity

**Limitations**:
- May produce severe load imbalance if depots are unevenly distributed
- No consideration of hotspot density
- Greedy assignment may produce suboptimal global solution

#### 3.3.3 Round-Robin Fallback

**Scenario**: Edge cases where primary algorithms fail or are inappropriate.

**Use Cases**:
- Vehicle count N ≥ hotspot count (some vehicles receive 0-1 hotspots)
- KMeans convergence failure or degenerate clustering
- Insufficient geographic variance for meaningful clustering

**Algorithm**: Sequential assignment hᵢ → vehicle (i mod N)

**Implementation Details**:
- Simple modulo-based assignment
- Preserves hotspot ordering
- Guarantees balanced assignment (difference ≤ 1)

**Advantages**:
- Always succeeds
- Predictable load balance
- Zero computational overhead

**Limitations**:
- Ignores geographic proximity
- May produce highly inefficient routes
- Should be avoided when possible

### 3.4 Load Imbalance Analysis

**Definition**: Load imbalance measures the uneven distribution of hotspots across vehicles.

**Metric**:
```
Load Imbalance = (max(partition_sizes) - min(partition_sizes)) / total_hotspots
```

**Interpretation**:
- 0.0: Perfectly balanced (all vehicles have equal hotspot counts)
- 1.0: Maximum imbalance (one vehicle has all hotspots)
- Typical acceptable range: 0.0 - 0.3 for practical N values

**Causes of Imbalance**:
- Uneven geographic distribution of crime hotspots
- Small hotspot count relative to vehicle count
- Multi-depot scenarios with clustered depots
- KMeans convergence to local optima

**Mitigation Strategies**:
- Minimum hotspot threshold before multi-vehicle routing
- Dynamic vehicle count adjustment based on hotspot density
- Post-partition balancing (move hotspots from overloaded partitions)
- Constraint-aware KMeans (minimum cluster size constraints)

### 3.5 Implementation Architecture

#### 3.5.1 Data Flow

```
Hotspot Database → HotspotPartitioner → RouteEngine → Multi-Vehicle Routes
                   ↓
              PartitionResult
                   ↓
           (vehicle_assignments, partition_sizes, fallback_used)
```

#### 3.5.2 API Integration

**Endpoint**: `POST /api/v1/patrol/compare`

**Request Parameters**:
```json
{
  "vehicle_count": 3,
  "hotspot_ids": ["uuid1", "uuid2", ...],
  "algorithm": "both"
}
```

**Response Structure**:
```json
{
  "generation_id": "uuid",
  "vehicle_count": 3,
  "routes": [
    {
      "vehicle_id": 0,
      "algorithm": "dijkstra",
      "waypoints": [...],
      "total_distance_km": 15.2,
      ...
    },
    ...
  ],
  "partition_metadata": {
    "partition_sizes": [5, 4, 3],
    "fallback_used": false,
    "load_imbalance": 0.133
  }
}
```

#### 3.5.3 Database Schema

**PatrolRoute Model Extension**:
```python
class PatrolRoute(db.Model):
    # Existing fields...
    vehicle_id = db.Column(db.Integer, nullable=True)  # Vehicle identifier
    generation_id = db.Column(db.String(36), nullable=True)  # UUID grouping
```

**Partition Metadata Storage**:
- Not persisted to database (transient for session)
- Logged for audit and analysis
- Available via API response for frontend display

### 3.6 Validation and Testing

#### 3.6.1 Unit Tests

**Test Coverage**:
- N=1 regression (must behave identically to single-vehicle)
- N > hotspot_count edge case
- KMeans clustering validity
- Multi-depot assignment correctness
- Round-robin fallback behavior
- Load imbalance calculation

**Test Data**:
- Synthetic hotspot distributions (uniform, clustered, linear)
- Real Harare hotspot data from production database
- Edge cases (duplicate coordinates, collinear points)

#### 3.6.2 Integration Tests

**Test Scenarios**:
- End-to-end multi-vehicle route generation
- API response structure validation
- Frontend display of partition metadata
- Database persistence of multi-vehicle routes

**Performance Benchmarks**:
- Computation time vs. vehicle count
- Load imbalance vs. hotspot distribution
- Total distance vs. single-vehicle baseline

### 3.7 Limitations and Future Work

#### 3.7.1 Current Limitations

1. **Decoupled Optimization**: Partition assignment and route ordering are optimized separately, missing potential joint improvements.

2. **Load Imbalance**: Geographic clustering may produce uneven workload distribution, especially for sparse hotspot distributions.

3. **No Inter-Vehicle Coordination**: Vehicles operate independently with no dynamic reassignment or load balancing during patrol.

4. **Static Vehicle Count**: N is predetermined rather than dynamically optimized based on hotspot density and geographic area.

5. **Single Objective**: Only distance minimization is considered; patrol timing, shift constraints, and vehicle availability are not modeled.

#### 3.7.2 Future Enhancements

1. **Joint VRP Optimization**: Implement true VRP solvers (e.g., OR-Tools, LKH) for optimal joint partition and route optimization.

2. **Constraint-Aware Partitioning**: Add minimum/maximum cluster size constraints to KMeans for better load balancing.

3. **Dynamic Vehicle Assignment**: Allow vehicles to be added/removed based on real-time workload and geographic coverage needs.

4. **Multi-Objective Optimization**: Incorporate fuel consumption, patrol timing, and officer shift constraints into the optimization objective.

5. **Real-Time Rebalancing**: Implement dynamic reassignment of hotspots between vehicles based on real-time incident patterns.

### 3.8 Conclusion

The geographic partitioning approach provides a practical, computationally efficient solution for multi-vehicle patrol routing in urban environments. By decoupling the partition assignment problem from the route optimization problem, we achieve:

- **Scalability**: Linear time complexity with respect to vehicle count
- **Simplicity**: Clear separation of concerns and easy implementation
- **Flexibility**: Support for both single-depot and multi-depot scenarios
- **Acceptable Performance**: Load imbalance within practical limits for real-world use

Empirical validation in Chapter 4 demonstrates that this approach produces patrol routes with acceptable efficiency and coverage for typical urban patrol scenarios in Harare, Zimbabwe.

---

**Key References**:
- Dantzig, G. B., & Ramser, J. H. (1959). The truck dispatching problem. Management Science.
- Lloyd, S. (1982). Least squares quantization in PCM. IEEE Transactions on Information Theory.
- Toth, P., & Vigo, D. (2014). The Vehicle Routing Problem. SIAM.
- sklearn.cluster.KMeans documentation: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html