"""
Unit tests for routing algorithms.
Tests manual Dijkstra and Genetic Algorithm implementations.
"""
import pytest
from app.services.routing.algorithms.dijkstra import dijkstra, select_lowest_cost_parallel_edge
from app.services.routing.algorithms.genetic_algorithm import GeneticAlgorithm, GAConfig, nearest_neighbour_ordering
from app.services.routing.route_service import RouteService


class TestDijkstra:
    """Test manual Dijkstra implementation."""
    
    def test_simple_path(self):
        """Test Dijkstra on a simple graph."""
        graph = {
            0: [{'v': 1, 'length_m': 100, 'key': 0}],
            1: [{'v': 2, 'length_m': 200, 'key': 0}],
            2: []
        }
        
        result = dijkstra(graph, 0, 2)
        
        assert result.status == 'success'
        assert result.path_node_ids == [0, 1, 2]
        assert result.total_distance_m == 300
        assert result.nodes_visited == 3
    
    def test_start_equals_end(self):
        """Test Dijkstra when start equals end."""
        graph = {0: [], 1: []}
        
        result = dijkstra(graph, 0, 0)
        
        assert result.status == 'start_equals_end'
        assert result.path_node_ids == [0]
        assert result.total_distance_m == 0
    
    def test_no_route(self):
        """Test Dijkstra when no path exists."""
        graph = {
            0: [{'v': 1, 'length_m': 100, 'key': 0}],
            1: [],
            2: []
        }
        
        result = dijkstra(graph, 0, 2)
        
        assert result.status == 'no_route'
        assert result.path_node_ids == []
        assert result.total_distance_m == float('inf')
    
    def test_parallel_edges(self):
        """Test Dijkstra with parallel edges selects lowest cost."""
        graph = {
            0: [
                {'v': 1, 'length_m': 100, 'key': 0},
                {'v': 1, 'length_m': 50, 'key': 1}
            ],
            1: []
        }
        
        result = dijkstra(graph, 0, 1)
        
        assert result.status == 'success'
        assert result.total_distance_m == 50  # Should select the shorter edge
    
    def test_directed_graph(self):
        """Test Dijkstra respects directed edges."""
        graph = {
            0: [{'v': 1, 'length_m': 100, 'key': 0}],
            1: []  # No edge back to 0
        }
        
        result_forward = dijkstra(graph, 0, 1)
        assert result_forward.status == 'success'
        
        result_backward = dijkstra(graph, 1, 0)
        assert result_backward.status == 'no_route'
    
    def test_select_lowest_cost_parallel_edge(self):
        """Test parallel edge selection."""
        graph = {
            0: [
                {'v': 1, 'length_m': 100, 'key': 0},
                {'v': 1, 'length_m': 50, 'key': 1},
                {'v': 1, 'length_m': 75, 'key': 2}
            ]
        }
        
        edge = select_lowest_cost_parallel_edge(graph, 0, 1)
        
        assert edge is not None
        assert edge['length_m'] == 50
        assert edge['key'] == 1


class TestGeneticAlgorithm:
    """Test manual Genetic Algorithm implementation."""
    
    def test_simple_case(self):
        """Test GA with simple distance matrix."""
        distance_matrix = [
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 10],
            [30, 25, 10, 0]
        ]
        
        config = GAConfig(
            population_size=10,
            generations=20,
            seed=42
        )
        
        ga = GeneticAlgorithm(distance_matrix, config)
        result = ga.solve()
        
        assert result.best_order[0] == 0  # Start is fixed
        assert len(result.best_order) == 4
        assert result.seed_used == 42
        assert len(result.convergence_history) == config.generations + 1
    
    def test_fixed_seed_reproducibility(self):
        """Test that fixed seed produces reproducible results."""
        distance_matrix = [
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0]
        ]
        
        config = GAConfig(population_size=5, generations=10, seed=123)
        
        ga1 = GeneticAlgorithm(distance_matrix, config)
        result1 = ga1.solve()
        
        ga2 = GeneticAlgorithm(distance_matrix, config)
        result2 = ga2.solve()
        
        assert result1.best_order == result2.best_order
        assert result1.best_distance == result2.best_distance
    
    def test_return_to_start(self):
        """Test GA can handle return to start via distance matrix."""
        distance_matrix = [
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0]
        ]
        
        config = GAConfig(population_size=5, generations=10, seed=42)
        ga = GeneticAlgorithm(distance_matrix, config)
        result = ga.solve()
        
        # Result order doesn't include return; that's handled by caller
        assert result.best_order[0] == 0
        assert len(set(result.best_order)) == len(distance_matrix)  # All stops visited once
    
    def test_population_bounds(self):
        """Test GA config bounds are enforced."""
        distance_matrix = [[0, 10], [10, 0]]
        
        # Test with extreme values
        config = GAConfig(
            population_size=1000,  # Should be capped
            generations=1000,  # Should be capped
            mutation_rate=2.0,  # Should be capped
            crossover_rate=2.0  # Should be capped
        )
        
        # The GA should handle these bounds internally
        ga = GeneticAlgorithm(distance_matrix, config)
        result = ga.solve()
        
        assert result.best_order is not None


class TestNearestNeighbour:
    """Test nearest-neighbor baseline algorithm."""
    
    def test_simple_ordering(self):
        """Test nearest-neighbor produces deterministic ordering."""
        distance_matrix = [
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 10],
            [30, 25, 10, 0]
        ]
        
        order = nearest_neighbour_ordering(distance_matrix)
        
        assert order[0] == 0  # Start is fixed
        assert len(order) == 4
        assert len(set(order)) == 4  # All nodes visited exactly once
    
    def test_deterministic_tie_breaking(self):
        """Test that ties are broken deterministically by index."""
        distance_matrix = [
            [0, 10, 10],  # Equal distances to nodes 1 and 2
            [10, 0, 10],
            [10, 10, 0]
        ]
        
        order = nearest_neighbour_ordering(distance_matrix)
        
        # Should pick node 1 first (lower index) due to tie-breaking
        assert order[1] == 1
    
    def test_two_nodes(self):
        """Test nearest-neighbor with two nodes."""
        distance_matrix = [
            [0, 10],
            [10, 0]
        ]
        
        order = nearest_neighbour_ordering(distance_matrix)
        
        assert order == [0, 1]


class TestRouteGeometry:
    def test_edge_geometries_are_stitched_in_route_order(self):
        service = RouteService.__new__(RouteService)
        service._nodes = {
            1: {'lat': 0.0, 'lng': 0.0},
            2: {'lat': 0.0, 'lng': 2.0},
            3: {'lat': 0.0, 'lng': 4.0},
        }
        service._graph = {
            1: [{'v': 2, 'key': 0, 'geometry_latlng': [[0.0, 0.0], [1.0, 0.5], [0.0, 2.0]]}],
            # Deliberately reversed to verify endpoint-based orientation.
            2: [{'v': 3, 'key': 0, 'geometry_latlng': [[0.0, 4.0], [-1.0, 3.5], [0.0, 2.0]]}],
        }

        geometry = service._reconstruct_geometry([1, 2, 3], [(1, 2, 0), (2, 3, 0)])

        assert geometry['coordinates'] == [
            [0.0, 0.0], [0.5, 1.0], [2.0, 0.0], [3.5, -1.0], [4.0, 0.0]
        ]
