# Multi-Vehicle Patrol Routing - Geographic Partitioning Approach

## Technical Description

The multi-vehicle routing extension implements a geographic pre-partitioning heuristic to distribute hotspot centroids among multiple patrol vehicles. The system employs K-means clustering to partition hotspots into N geographic zones, where N corresponds to the number of available vehicles. Each vehicle then independently routes through its assigned zone using the existing single-vehicle Genetic Algorithm and Dijkstra implementations unchanged.

The partitioning module supports both single-depot and multi-depot scenarios. In single-depot mode, all vehicles share the same starting location (police station), and K-means++ initialization is used for geographic clustering. In multi-depot mode, vehicles start from different sub-depot locations, and cluster centers are initialized near each depot to bias the geographic partitioning toward each vehicle's starting point.

This approach represents a heuristic decoupling of partition assignment and route ordering, not a joint optimization. The system does not guarantee load-balanced routes across vehicles, as geographic clustering may assign uneven numbers of hotspots based on spatial distribution. Load imbalance is an expected limitation of this heuristic approach.

## Implementation Details

- **Partitioning Algorithm**: K-means clustering with configurable random state for reproducibility
- **Fallback Mechanism**: Round-robin assignment for edge cases (N ≥ hotspot count, degenerate clustering)
- **Multi-Depot Support**: Cluster initialization near depot locations when sub-depots are specified
- **Edge Case Handling**: N=1 bypasses partitioning entirely; N ≤ 0 raises validation errors
- **Assignment Validation**: Every hotspot assigned to exactly one vehicle (no duplicates, no omissions)

## Validation Results

Partition size validation on realistic Harare hotspot data (15 hotspots):

| Vehicles | Partition Sizes | Load Imbalance | Fallback Used |
|----------|----------------|----------------|---------------|
| 1        | 15             | 0.0%           | No            |
| 2        | 9, 6           | 20.0%          | No            |
| 3        | 6, 6, 3        | 20.0%          | No            |
| 5        | 3, 3, 3, 3, 3  | 0.0%           | No            |

Multi-depot validation (2 sub-depots): Partition sizes [12, 3], load imbalance 60.0%

The validation confirms that all hotspots are assigned to exactly one vehicle, geographic clustering produces sensible spatial partitions, and load imbalance varies based on hotspot distribution and depot placement.

## Design Assumptions

- Vehicles may start from different sub-depot locations within a station's jurisdiction
- Geographic clustering is weighted toward each vehicle's actual starting point in multi-depot scenarios
- Single-depot mode assumes all vehicles share the same starting location
- Load imbalance across vehicles is acceptable and expected for heuristic partitioning

## Limitations

- No joint optimization of partition assignment and route order (full VRP)
- No load-balancing logic based on route cost
- Geographic clustering may produce uneven partitions based on hotspot spatial distribution
- Sequential execution of vehicle routing algorithms (no parallelization)

## Future Work

Full joint multi-vehicle optimization (Vehicle Routing Problem) is identified as future work. This would require encoding vehicle assignment and visiting order in a single chromosome, redesigned crossover/mutation operators, and a fitness function that explicitly balances total fleet cost versus maximum single-vehicle cost.