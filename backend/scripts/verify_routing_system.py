"""
Manual Verification Script for Road Network Routing System

This script performs manual verification and performance measurements
for the dissertation. Run this after generating the OSM graph with
the preprocessor.

Usage:
    python scripts/verify_routing_system.py

Output:
    - Verification report with performance metrics
    - Route quality checks
    - Sanity test results
"""
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.routing import graph_store, route_service
from app.services.routing.algorithms import dijkstra, GeneticAlgorithm, GAConfig, nearest_neighbour_ordering

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Known Harare coordinates for sanity testing
HARARE_TEST_POINTS = {
    'cbd_center': {'lat': -17.8292, 'lng': 31.0522},
    'cbd_west': {'lat': -17.8252, 'lng': 31.0475},
    'cbd_east': {'lat': -17.8189, 'lng': 31.0433},
    'suburb_borrowdale': {'lat': -17.7847, 'lng': 31.0722},
    'suburb_mabelreign': {'lat': -17.7958, 'lng': 31.0289}
}


def verify_graph_loading() -> Dict[str, Any]:
    """Verify graph can be loaded and check metadata."""
    logger.info("=" * 60)
    logger.info("Verifying Graph Loading")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    try:
        # Reset to test fresh load
        graph_store.reset()
        
        # Get graph (triggers load)
        graph, nodes = graph_store.get_graph()
        
        load_time = time.time() - start_time
        
        # Get status
        status = graph_store.get_status()
        
        results = {
            'success': True,
            'load_time_seconds': load_time,
            'status': status,
            'nodes_loaded': len(nodes),
            'edges_loaded': sum(len(edges) for edges in graph.values())
        }
        
        logger.info(f"Graph loaded successfully in {load_time:.2f}s")
        logger.info(f"Nodes: {results['nodes_loaded']}, Edges: {results['edges_loaded']}")
        logger.info(f"Memory: {status['memory_bytes'] / 1024 / 1024:.2f} MB")
        
        return results
        
    except Exception as e:
        logger.error(f"Graph loading failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'load_time_seconds': time.time() - start_time
        }


def verify_spatial_index() -> Dict[str, Any]:
    """Verify spatial index and point snapping."""
    logger.info("=" * 60)
    logger.info("Verifying Spatial Index")
    logger.info("=" * 60)
    
    try:
        from app.services.routing import SpatialIndex
        
        graph, nodes = graph_store.get_graph()
        
        start_time = time.time()
        index = SpatialIndex(nodes)
        build_time = time.time() - start_time
        
        # Test snapping with known points
        snap_results = {}
        for name, coords in HARARE_TEST_POINTS.items():
            snap_start = time.time()
            result = index.find_nearest_node(coords['lat'], coords['lng'])
            snap_time = (time.time() - snap_start) * 1000
            
            snap_results[name] = {
                'success': result is not None,
                'snap_distance_m': result.snap_distance_m if result else None,
                'query_time_ms': snap_time
            }
            
            if result:
                logger.info(f"{name}: snapped to node {result.node_id}, distance {result.snap_distance_m:.1f}m")
            else:
                logger.warning(f"{name}: snap failed (point too far from network)")
        
        return {
            'success': True,
            'build_time_seconds': build_time,
            'snap_results': snap_results
        }
        
    except Exception as e:
        logger.error(f"Spatial index verification failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def verify_dijkstra_performance() -> Dict[str, Any]:
    """Verify Dijkstra algorithm performance and correctness."""
    logger.info("=" * 60)
    logger.info("Verifying Dijkstra Algorithm")
    logger.info("=" * 60)
    
    try:
        graph, nodes = graph_store.get_graph()
        
        # Get test node IDs
        from app.services.routing import SpatialIndex
        index = SpatialIndex(nodes)
        
        cbd_center = index.find_nearest_node(
            HARARE_TEST_POINTS['cbd_center']['lat'],
            HARARE_TEST_POINTS['cbd_center']['lng']
        )
        cbd_west = index.find_nearest_node(
            HARARE_TEST_POINTS['cbd_west']['lat'],
            HARARE_TEST_POINTS['cbd_west']['lng']
        )
        
        if not cbd_center or not cbd_west:
            return {
                'success': False,
                'error': 'Could not snap test points to graph'
            }
        
        # Run Dijkstra
        start_time = time.time()
        result = dijkstra(graph, cbd_center.node_id, cbd_west.node_id)
        query_time = (time.time() - start_time) * 1000
        
        logger.info(f"Dijkstra query completed in {query_time:.2f}ms")
        logger.info(f"Path length: {result.total_distance_m:.1f}m")
        logger.info(f"Nodes visited: {result.nodes_visited}")
        logger.info(f"Path nodes: {len(result.path_node_ids)}")
        
        # Sanity checks
        if result.status == 'success':
            assert result.total_distance_m > 0, "Distance should be positive"
            assert len(result.path_node_ids) >= 2, "Path should have at least start and end"
            assert result.path_node_ids[0] == cbd_center.node_id, "Path should start at correct node"
            assert result.path_node_ids[-1] == cbd_west.node_id, "Path should end at correct node"
        
        return {
            'success': True,
            'status': result.status,
            'query_time_ms': query_time,
            'total_distance_m': result.total_distance_m,
            'nodes_visited': result.nodes_visited,
            'path_length': len(result.path_node_ids)
        }
        
    except Exception as e:
        logger.error(f"Dijkstra verification failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def verify_ga_performance() -> Dict[str, Any]:
    """Verify Genetic Algorithm performance and convergence."""
    logger.info("=" * 60)
    logger.info("Verifying Genetic Algorithm")
    logger.info("=" * 60)
    
    try:
        # Create a test distance matrix
        # Use known points to create realistic matrix
        from app.services.routing import SpatialIndex
        graph, nodes = graph_store.get_graph()
        index = SpatialIndex(nodes)
        
        # Get 4 test points
        test_points = list(HARARE_TEST_POINTS.values())[:4]
        snapped = []
        for point in test_points:
            snap = index.find_nearest_node(point['lat'], point['lng'])
            if snap:
                snapped.append(snap)
        
        if len(snapped) < 4:
            return {
                'success': False,
                'error': f'Could only snap {len(snapped)} points (need 4)'
            }
        
        # Build distance matrix
        distance_matrix = [[0.0] * len(snapped) for _ in range(len(snapped))]
        for i in range(len(snapped)):
            for j in range(len(snapped)):
                if i != j:
                    result = dijkstra(graph, snapped[i].node_id, snapped[j].node_id)
                    if result.status == 'success':
                        distance_matrix[i][j] = result.total_distance_m
                    else:
                        distance_matrix[i][j] = float('inf')
        
        # Test baseline
        baseline_start = time.time()
        baseline_order = nearest_neighbour_ordering(distance_matrix)
        baseline_time = (time.time() - baseline_start) * 1000
        baseline_distance = sum(
            distance_matrix[baseline_order[i]][baseline_order[i+1]]
            for i in range(len(baseline_order) - 1)
        )
        
        logger.info(f"Baseline (nearest-neighbor): {baseline_distance:.1f}m, {baseline_time:.2f}ms")
        
        # Test GA
        config = GAConfig(
            population_size=50,
            generations=100,
            seed=42
        )
        
        ga_start = time.time()
        ga = GeneticAlgorithm(distance_matrix, config)
        ga_result = ga.solve()
        ga_time = (time.time() - ga_start) * 1000
        
        logger.info(f"GA: {ga_result.best_distance:.1f}m, {ga_time:.2f}ms")
        logger.info(f"Generations: {ga_result.generations_completed}")
        logger.info(f"Convergence: {ga_result.convergence_history[:5]}...{ga_result.convergence_history[-5:]}")
        
        # Calculate improvement
        if baseline_distance > 0:
            improvement = (baseline_distance - ga_result.best_distance) / baseline_distance * 100
            logger.info(f"GA improvement: {improvement:.2f}%")
        
        return {
            'success': True,
            'baseline_distance_m': baseline_distance,
            'baseline_time_ms': baseline_time,
            'ga_distance_m': ga_result.best_distance,
            'ga_time_ms': ga_time,
            'ga_generations': ga_result.generations_completed,
            'improvement_pct': (baseline_distance - ga_result.best_distance) / baseline_distance * 100 if baseline_distance > 0 else 0,
            'convergence_sample': ga_result.convergence_history[:10]
        }
        
    except Exception as e:
        logger.error(f"GA verification failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def run_sanity_check() -> Dict[str, Any]:
    """Run basic sanity check with known Harare route."""
    logger.info("=" * 60)
    logger.info("Running Sanity Check")
    logger.info("=" * 60)
    
    try:
        # Test a simple CBD route
        request = route_service.validate_point_to_point_request({
            'city': 'harare',
            'start': HARARE_TEST_POINTS['cbd_center'],
            'end': HARARE_TEST_POINTS['cbd_west'],
            'algorithm': 'dijkstra'
        })
        
        result = route_service.compute_point_to_point_route(request)
        
        logger.info(f"Sanity check route: {result.total_distance_m:.1f}m")
        logger.info(f"Execution time: {result.execution_time_ms:.2f}ms")
        logger.info(f"Start snap: {result.start_snap_distance_m:.1f}m")
        logger.info(f"End snap: {result.end_snap_distance_m:.1f}m")
        
        # Sanity check: CBD route should be reasonable
        # CBD to CBD west should be roughly 1-3 km
        if 500 < result.total_distance_m < 5000:
            logger.info("✓ Distance within expected range for CBD route")
            distance_sane = True
        else:
            logger.warning(f"✗ Distance {result.total_distance_m:.1f}m seems unusual for CBD route")
            distance_sane = False
        
        return {
            'success': True,
            'distance_m': result.total_distance_m,
            'execution_time_ms': result.execution_time_ms,
            'distance_sane': distance_sane
        }
        
    except Exception as e:
        logger.error(f"Sanity check failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Run all verification tests and generate report."""
    logger.info("Starting Road Network Routing System Verification")
    logger.info("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'graph_loading': verify_graph_loading(),
        'spatial_index': verify_spatial_index(),
        'dijkstra': verify_dijkstra_performance(),
        'genetic_algorithm': verify_ga_performance(),
        'sanity_check': run_sanity_check()
    }
    
    # Generate summary
    logger.info("=" * 60)
    logger.info("Verification Summary")
    logger.info("=" * 60)
    
    total_tests = len(report)
    passed_tests = sum(1 for v in report.values() if isinstance(v, dict) and v.get('success', False))
    
    logger.info(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        logger.info("✓ All verification tests passed")
    else:
        logger.warning(f"✗ {total_tests - passed_tests} test(s) failed")
    
    # Save report
    report_path = Path(__file__).parent.parent / 'ml' / 'routing' / 'verification_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {report_path}")
    
    return report


if __name__ == '__main__':
    main()
