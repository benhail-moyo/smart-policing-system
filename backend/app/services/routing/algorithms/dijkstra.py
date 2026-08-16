"""
Manual Dijkstra implementation using heapq for point-to-point shortest path.
This is a true Dijkstra algorithm for road network routing, not the nearest-neighbor
baseline that exists in dijkstra_solver.py.
"""
import heapq
import time
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class DijkstraResult:
    """Result of Dijkstra shortest path computation."""
    path_node_ids: List[int]  # Ordered list of node IDs in the path
    edge_keys: List[Tuple[int, int, int]]  # (u, v, key) for each edge in path
    total_distance_m: float  # Total distance in metres
    nodes_visited: int  # Number of nodes visited during search
    execution_time_ms: float  # Execution time in milliseconds
    status: str  # 'success', 'no_route', 'start_equals_end'


def dijkstra(
    graph: Dict[int, List[Dict]],
    start_node: int,
    end_node: int,
    edge_weight_key: str = 'length_m'
) -> DijkstraResult:
    """
    Run Dijkstra's algorithm on a directed graph using heapq.
    
    Args:
        graph: Adjacency list representation {node_id: [edge_dict, ...]}
               Each edge_dict must contain: 'v' (target node), edge_weight_key, 'key' (edge identifier)
        start_node: Starting node ID
        end_node: Target node ID
        edge_weight_key: Key to use for edge weight (default: 'length_m')
    
    Returns:
        DijkstraResult with path, distance, and performance metrics
    """
    start_time = time.perf_counter()
    
    # Handle special case: start equals end
    if start_node == end_node:
        return DijkstraResult(
            path_node_ids=[start_node],
            edge_keys=[],
            total_distance_m=0.0,
            nodes_visited=1,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
            status='start_equals_end'
        )
    
    # Initialize data structures
    distances: Dict[int, float] = {start_node: 0.0}
    previous: Dict[int, Tuple[int, int, int]] = {}  # node -> (prev_node, target_node, edge_key)
    visited: Set[int] = set()
    nodes_visited = 0
    
    # Priority queue: (distance, node_id)
    pq: List[Tuple[float, int]] = [(0.0, start_node)]
    
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        # Skip if we've already found a better path
        if current_node in visited:
            continue
        
        visited.add(current_node)
        nodes_visited += 1
        
        # Found the target
        if current_node == end_node:
            break
        
        # Explore neighbors
        if current_node not in graph:
            continue
            
        for edge in graph[current_node]:
            neighbor = edge['v']
            edge_weight = edge.get(edge_weight_key, float('inf'))
            edge_key = edge.get('key', 0)
            
            if edge_weight == float('inf'):
                continue
                
            new_dist = current_dist + edge_weight
            
            # Relaxation step
            if neighbor not in distances or new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = (current_node, neighbor, edge_key)
                heapq.heappush(pq, (new_dist, neighbor))
    
    execution_time_ms = (time.perf_counter() - start_time) * 1000
    
    # Check if we found a path
    if end_node not in previous and start_node != end_node:
        return DijkstraResult(
            path_node_ids=[],
            edge_keys=[],
            total_distance_m=float('inf'),
            nodes_visited=nodes_visited,
            execution_time_ms=execution_time_ms,
            status='no_route'
        )
    
    # Reconstruct path
    path_node_ids = []
    edge_keys = []
    
    if end_node in previous or start_node == end_node:
        # Reconstruct backwards from end to start
        current = end_node
        path_rev = [current]
        
        while current != start_node:
            if current not in previous:
                break
            prev_node, _, edge_key = previous[current]
            edge_keys.append((prev_node, current, edge_key))
            current = prev_node
            path_rev.append(current)
        
        path_node_ids = list(reversed(path_rev))
        edge_keys = list(reversed(edge_keys))
    
    total_distance = distances.get(end_node, float('inf'))
    
    return DijkstraResult(
        path_node_ids=path_node_ids,
        edge_keys=edge_keys,
        total_distance_m=total_distance,
        nodes_visited=nodes_visited,
        execution_time_ms=execution_time_ms,
        status='success' if path_node_ids else 'no_route'
    )


def select_lowest_cost_parallel_edge(
    graph: Dict[int, List[Dict]],
    u: int,
    v: int,
    edge_weight_key: str = 'length_m'
) -> Optional[Dict]:
    """
    Select the lowest-cost parallel edge between u and v.
    
    Args:
        graph: Adjacency list representation
        u: Source node ID
        v: Target node ID
        edge_weight_key: Key to use for edge weight comparison
    
    Returns:
        The edge dict with the lowest cost, or None if no edge exists
    """
    if u not in graph:
        return None
    
    candidate_edges = [edge for edge in graph[u] if edge['v'] == v]
    
    if not candidate_edges:
        return None
    
    # Select edge with minimum weight
    return min(candidate_edges, key=lambda e: e.get(edge_weight_key, float('inf')))
