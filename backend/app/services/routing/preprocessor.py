"""
OSM Preprocessor for Harare Road Network Graph

This is a one-off command/script for preprocessing OpenStreetMap data
to create a directed road network graph for routing.

Usage:
    python run_preprocessor.py (from backend directory)

Output:
    - backend/ml/routing/data/harare_drive_graph.json.gz (compressed graph)
    - backend/ml/routing/data/harare_drive_graph_metadata.json (metadata)
"""
import gzip
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

try:
    import osmnx as ox
    import networkx as nx
    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False
    logging.warning("osmnx not available - full OSM preprocessing disabled")

logger = logging.getLogger(__name__)

# Harare bounding box (approximate)
HARARE_BOUNDS = {
    'north': -17.7,
    'south': -17.9,
    'east': 31.2,
    'west': 31.0
}

# OSM source URL (Geofabrik Zimbabwe extract)
OSM_SOURCE_URL = "https://download.geofabrik.de/africa/zimbabwe-latest.osm.pbf"
OSM_SOURCE_DATE = "2024-01-01"  # Update this when using actual data


def download_osm_extract(output_path: Path) -> Path:
    """
    Download OSM PBF extract for Zimbabwe.
    
    Note: This is a placeholder. In production, you would:
    1. Download the actual PBF file from Geofabrik
    2. Or use a local OSM PBF file
    
    For this implementation, we'll use osmnx to download directly for Harare.
    """
    logger.info(f"OSM extract would be downloaded to {output_path}")
    logger.info(f"Source: {OSM_SOURCE_URL}")
    return output_path


def extract_harare_graph() -> nx.MultiDiGraph:
    """
    Extract drivable road network for Harare using OSMnx.
    
    Returns:
        NetworkX MultiDiGraph of the Harare road network
    """
    if not OSMNX_AVAILABLE:
        raise ImportError("osmnx is required for OSM graph extraction. Install with: pip install osmnx==1.9.1")
    
    logger.info("Extracting Harare road network from OSM...")
    
    # Use OSMnx to download and filter the drivable network
    # Define Harare bounding box
    north, south, east, west = (
        HARARE_BOUNDS['north'],
        HARARE_BOUNDS['south'],
        HARARE_BOUNDS['east'],
        HARARE_BOUNDS['west']
    )
    
    # Download drivable network
    logger.info(f"Downloading OSM data for bounds: {west},{south},{east},{north}")
    graph = ox.graph_from_bbox(
        north, south, east, west,
        network_type='drive',
        simplify=True,
        retain_all=True,
        truncate_by_edge=True
    )
    
    logger.info(f"Extracted graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    
    return graph


def preprocess_graph(graph: nx.MultiDiGraph) -> Tuple[nx.MultiDiGraph, Dict[str, Any]]:
    """
    Preprocess the graph: filter to largest weakly connected component,
    clean node/edge attributes, and prepare for serialization.
    
    Args:
        graph: Raw OSMnx graph
    
    Returns:
        Tuple of (processed graph, preprocessing metadata)
    """
    logger.info("Preprocessing graph...")
    start_time = time.time()
    
    initial_nodes = graph.number_of_nodes()
    initial_edges = graph.number_of_edges()
    
    # Get largest weakly connected component
    # We use weakly connected (not strongly) to include cul-de-sacs and one-way access roads
    logger.info("Extracting largest weakly connected component...")
    largest_cc = max(nx.weakly_connected_components(graph), key=len)
    graph = graph.subgraph(largest_cc).copy()
    
    logger.info(
        f"Largest component: {graph.number_of_nodes()} nodes, "
        f"{graph.number_of_edges()} edges "
        f"(removed {initial_nodes - graph.number_of_nodes()} nodes, "
        f"{initial_edges - graph.number_of_edges()} edges)"
    )
    
    # Ensure graph is properly directed
    graph = nx.MultiDiGraph(graph)
    
    # Clean and standardize node attributes
    # First, collect nodes to remove (avoid modifying during iteration)
    nodes_to_remove = []
    for node_id, node_data in graph.nodes(data=True):
        # Check for lat/lon using both attribute names OSMnx might use
        has_lat = 'lat' in node_data or 'y' in node_data
        has_lon = 'lon' in node_data or 'x' in node_data
        
        if not has_lat or not has_lon:
            logger.warning(f"Node {node_id} missing lat/lon, removing")
            nodes_to_remove.append(node_id)
    
    # Remove invalid nodes
    for node_id in nodes_to_remove:
        graph.remove_node(node_id)
    
    # Standardize attribute names for remaining nodes
    for node_id, node_data in graph.nodes(data=True):
        # Handle both OSMnx attribute naming conventions
        lat = node_data.get('lat', node_data.get('y'))
        lon = node_data.get('lon', node_data.get('x'))
        
        if lat is not None and lon is not None:
            node_data['lat'] = float(lat)
            node_data['lng'] = float(lon)  # Convert 'lon' to 'lng'
            
            # Clean up alternative attribute names
            if 'y' in node_data:
                del node_data['y']
            if 'x' in node_data:
                del node_data['x']
            if 'lon' in node_data:
                del node_data['lon']
    
    # Clean and standardize edge attributes
    for u, v, key, edge_data in graph.edges(keys=True, data=True):
        # Calculate edge length if not present
        if 'length' not in edge_data:
            # Calculate length from geometry or node coordinates
            if 'geometry' in edge_data:
                # Use shapely geometry length
                edge_data['length'] = edge_data['geometry'].length
            else:
                # Calculate from node coordinates
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]
                # Use our standardized attribute names
                u_lat = u_data.get('lat', u_data.get('y'))
                u_lng = u_data.get('lng', u_data.get('x'))
                v_lat = v_data.get('lat', v_data.get('y'))
                v_lng = v_data.get('lng', v_data.get('x'))
                
                if u_lat and u_lng and v_lat and v_lng:
                    edge_data['length'] = ox.distance.great_circle_vec(
                        u_lat, u_lng, v_lat, v_lng
                    )
                else:
                    # Fallback to a default length if coordinates are missing
                    edge_data['length'] = 100.0  # 100m default
        
        # Standardize attribute names
        edge_data['length_m'] = float(edge_data.get('length', 100.0))
        if 'length' in edge_data:
            del edge_data['length']
        
        # Extract geometry as lat/lng list
        if 'geometry' in edge_data:
            geometry = edge_data['geometry']
            if hasattr(geometry, 'coords'):
                edge_data['geometry_latlng'] = [[lat, lng] for lng, lat in geometry.coords]
            else:
                edge_data['geometry_latlng'] = []
            del edge_data['geometry']
        else:
            edge_data['geometry_latlng'] = []
        
        # Preserve other useful attributes
        edge_data['highway'] = edge_data.get('highway', 'unclassified')
        edge_data['name'] = edge_data.get('name', '')
        edge_data['maxspeed'] = edge_data.get('maxspeed', '')
        edge_data['oneway'] = edge_data.get('oneway', False)
    
    preprocessing_time = time.time() - start_time
    
    metadata = {
        'initial_nodes': initial_nodes,
        'initial_edges': initial_edges,
        'final_nodes': graph.number_of_nodes(),
        'final_edges': graph.number_of_edges(),
        'weak_components': nx.number_weakly_connected_components(graph),
        'preprocessing_time_seconds': preprocessing_time,
    }
    
    logger.info(f"Preprocessing completed in {preprocessing_time:.2f}s")
    
    return graph, metadata


def serialize_graph(
    graph: nx.MultiDiGraph,
    preprocessing_metadata: Dict[str, Any],
    output_dir: Path
) -> Tuple[Path, Path]:
    """
    Serialize the graph to compressed JSON format.
    
    Args:
        graph: Processed NetworkX graph
        preprocessing_metadata: Metadata from preprocessing
        output_dir: Directory to save output files
    
    Returns:
        Tuple of (graph_file_path, metadata_file_path)
    """
    logger.info("Serializing graph...")
    start_time = time.time()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to adjacency list format
    adjacency_list = {}
    for u in graph.nodes():
        edges = []
        # Use the correct iteration method for MultiDiGraph
        for _, v, key, edge_data in graph.out_edges(u, keys=True, data=True):
            edge_dict = {
                'v': int(v),
                'key': int(key),
                'length_m': float(edge_data.get('length_m', 0)),
                'geometry_latlng': edge_data.get('geometry_latlng', []),
                'highway': edge_data.get('highway', ''),
                'name': edge_data.get('name', ''),
                'maxspeed': edge_data.get('maxspeed', ''),
                'oneway': edge_data.get('oneway', False)
            }
            edges.append(edge_dict)
        adjacency_list[int(u)] = edges
    
    # Convert nodes to simple format
    nodes_dict = {}
    for node_id, node_data in graph.nodes(data=True):
        nodes_dict[int(node_id)] = {
            'lat': float(node_data['lat']),
            'lng': float(node_data['lng'])
        }
    
    # Create graph data structure
    graph_data = {
        'graph': adjacency_list,
        'nodes': nodes_dict
    }
    
    # Save compressed graph
    graph_file = output_dir / 'harare_drive_graph.json.gz'
    with gzip.open(graph_file, 'wt', encoding='utf-8') as f:
        json.dump(graph_data, f)
    
    # Create metadata
    metadata = {
        'version': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'city': 'harare',
        'osm_source_url': OSM_SOURCE_URL,
        'osm_source_date': OSM_SOURCE_DATE,
        'crop_bounds': HARARE_BOUNDS,
        'preprocessing_date': datetime.now().isoformat(),
        'nodes': len(nodes_dict),
        'directed_edges': sum(len(edges) for edges in adjacency_list.values()),
        'preprocessing_metadata': preprocessing_metadata,
        'artifact_size_bytes': graph_file.stat().st_size
    }
    
    # Save metadata
    metadata_file = output_dir / 'harare_drive_graph_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    serialization_time = time.time() - start_time
    
    logger.info(
        f"Graph serialized: {graph_file} ({graph_file.stat().st_size / 1024 / 1024:.2f} MB), "
        f"metadata: {metadata_file}, "
        f"time: {serialization_time:.2f}s"
    )
    
    return graph_file, metadata_file


def main():
    """Main preprocessing pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 60)
    logger.info("OSM Preprocessor for Harare Road Network")
    logger.info("=" * 60)
    
    if not OSMNX_AVAILABLE:
        logger.error("osmnx is not installed. Please install it with: pip install osmnx==1.9.1")
        logger.info("For testing purposes, you can create a synthetic test graph using:")
        logger.info("  python scripts/create_test_graph.py")
        return
    
    total_start = time.time()
    
    try:
        # Step 1: Extract graph
        graph = extract_harare_graph()
        
        # Step 2: Preprocess
        processed_graph, preprocessing_metadata = preprocess_graph(graph)
        
        # Step 3: Serialize
        output_dir = Path(__file__).parent.parent.parent.parent / 'ml' / 'routing' / 'data'
        graph_file, metadata_file = serialize_graph(
            processed_graph,
            preprocessing_metadata,
            output_dir
        )
        
        total_time = time.time() - total_start
        
        logger.info("=" * 60)
        logger.info("Preprocessing completed successfully!")
        logger.info(f"Total time: {total_time:.2f}s")
        logger.info(f"Graph file: {graph_file}")
        logger.info(f"Metadata file: {metadata_file}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
