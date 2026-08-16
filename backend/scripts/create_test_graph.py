"""
Create a minimal test graph for development and testing.
This creates a small synthetic graph to test the routing system
without requiring OSM data download.
"""
import gzip
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_graph():
    """Create a minimal test graph for Harare area."""
    logger.info("Creating minimal test graph...")
    
    # Create a small synthetic graph representing a simplified Harare street network
    # This is for testing purposes only - not for production use
    
    # Nodes: key points in Harare CBD area
    nodes = {
        0: {'lat': -17.8292, 'lng': 31.0522},  # CBD center
        1: {'lat': -17.8252, 'lng': 31.0475},  # CBD west
        2: {'lat': -17.8189, 'lng': 31.0433},  # CBD east
        3: {'lat': -17.8216, 'lng': 31.0492},  # CBD north
        4: {'lat': -17.8320, 'lng': 31.0550},  # CBD south
        5: {'lat': -17.7847, 'lng': 31.0722},  # Borrowdale area
        6: {'lat': -17.7958, 'lng': 31.0289},  # Mabelreign area
    }
    
    # Edges: simplified street connections with approximate distances
    graph = {
        0: [
            {'v': 1, 'key': 0, 'length_m': 600, 'geometry_latlng': [[-17.8292, 31.0522], [-17.8252, 31.0475]], 'highway': 'primary', 'name': 'Samora Machel Ave', 'maxspeed': '60', 'oneway': False},
            {'v': 2, 'key': 0, 'length_m': 800, 'geometry_latlng': [[-17.8292, 31.0522], [-17.8189, 31.0433]], 'highway': 'primary', 'name': 'Jason Moyo Ave', 'maxspeed': '60', 'oneway': False},
            {'v': 3, 'key': 0, 'length_m': 400, 'geometry_latlng': [[-17.8292, 31.0522], [-17.8216, 31.0492]], 'highway': 'secondary', 'name': 'Nelson Mandela Ave', 'maxspeed': '50', 'oneway': False},
            {'v': 4, 'key': 0, 'length_m': 500, 'geometry_latlng': [[-17.8292, 31.0522], [-17.8320, 31.0550]], 'highway': 'secondary', 'name': 'Kwame Nkrumah Ave', 'maxspeed': '50', 'oneway': False},
        ],
        1: [
            {'v': 0, 'key': 0, 'length_m': 600, 'geometry_latlng': [[-17.8252, 31.0475], [-17.8292, 31.0522]], 'highway': 'primary', 'name': 'Samora Machel Ave', 'maxspeed': '60', 'oneway': False},
            {'v': 2, 'key': 0, 'length_m': 700, 'geometry_latlng': [[-17.8252, 31.0475], [-17.8189, 31.0433]], 'highway': 'secondary', 'name': 'Second St', 'maxspeed': '50', 'oneway': False},
            {'v': 6, 'key': 0, 'length_m': 2500, 'geometry_latlng': [[-17.8252, 31.0475], [-17.7958, 31.0289]], 'highway': 'primary', 'name': 'Lomagundi Rd', 'maxspeed': '80', 'oneway': False},
        ],
        2: [
            {'v': 0, 'key': 0, 'length_m': 800, 'geometry_latlng': [[-17.8189, 31.0433], [-17.8292, 31.0522]], 'highway': 'primary', 'name': 'Jason Moyo Ave', 'maxspeed': '60', 'oneway': False},
            {'v': 1, 'key': 0, 'length_m': 700, 'geometry_latlng': [[-17.8189, 31.0433], [-17.8252, 31.0475]], 'highway': 'secondary', 'name': 'Second St', 'maxspeed': '50', 'oneway': False},
            {'v': 5, 'key': 0, 'length_m': 3000, 'geometry_latlng': [[-17.8189, 31.0433], [-17.7847, 31.0722]], 'highway': 'primary', 'name': 'Rebecca Ave', 'maxspeed': '80', 'oneway': False},
        ],
        3: [
            {'v': 0, 'key': 0, 'length_m': 400, 'geometry_latlng': [[-17.8216, 31.0492], [-17.8292, 31.0522]], 'highway': 'secondary', 'name': 'Nelson Mandela Ave', 'maxspeed': '50', 'oneway': False},
            {'v': 5, 'key': 0, 'length_m': 2800, 'geometry_latlng': [[-17.8216, 31.0492], [-17.7847, 31.0722]], 'highway': 'primary', 'name': 'Enterprise Rd', 'maxspeed': '80', 'oneway': False},
        ],
        4: [
            {'v': 0, 'key': 0, 'length_m': 500, 'geometry_latlng': [[-17.8320, 31.0550], [-17.8292, 31.0522]], 'highway': 'secondary', 'name': 'Kwame Nkrumah Ave', 'maxspeed': '50', 'oneway': False},
            {'v': 6, 'key': 0, 'length_m': 2200, 'geometry_latlng': [[-17.8320, 31.0550], [-17.7958, 31.0289]], 'highway': 'primary', 'name': 'Cowan Rd', 'maxspeed': '80', 'oneway': False},
        ],
        5: [
            {'v': 2, 'key': 0, 'length_m': 3000, 'geometry_latlng': [[-17.7847, 31.0722], [-17.8189, 31.0433]], 'highway': 'primary', 'name': 'Rebecca Ave', 'maxspeed': '80', 'oneway': False},
            {'v': 3, 'key': 0, 'length_m': 2800, 'geometry_latlng': [[-17.7847, 31.0722], [-17.8216, 31.0492]], 'highway': 'primary', 'name': 'Enterprise Rd', 'maxspeed': '80', 'oneway': False},
        ],
        6: [
            {'v': 1, 'key': 0, 'length_m': 2500, 'geometry_latlng': [[-17.7958, 31.0289], [-17.8252, 31.0475]], 'highway': 'primary', 'name': 'Lomagundi Rd', 'maxspeed': '80', 'oneway': False},
            {'v': 4, 'key': 0, 'length_m': 2200, 'geometry_latlng': [[-17.7958, 31.0289], [-17.8320, 31.0550]], 'highway': 'primary', 'name': 'Cowan Rd', 'maxspeed': '80', 'oneway': False},
        ],
    }
    
    # Create graph data structure
    graph_data = {
        'graph': graph,
        'nodes': nodes
    }
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent.parent / 'ml' / 'routing' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save compressed graph
    graph_file = output_dir / 'harare_drive_graph.json.gz'
    with gzip.open(graph_file, 'wt', encoding='utf-8') as f:
        json.dump(graph_data, f)
    
    # Create metadata
    metadata = {
        'version': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'city': 'harare',
        'osm_source_url': 'TEST_GRAPH_SYNTHETIC',
        'osm_source_date': datetime.now().isoformat(),
        'crop_bounds': {
            'north': -17.78,
            'south': -17.84,
            'east': 31.08,
            'west': 31.02
        },
        'preprocessing_date': datetime.now().isoformat(),
        'nodes': len(nodes),
        'directed_edges': sum(len(edges) for edges in graph.values()),
        'preprocessing_metadata': {
            'initial_nodes': len(nodes),
            'initial_edges': sum(len(edges) for edges in graph.values()),
            'final_nodes': len(nodes),
            'final_edges': sum(len(edges) for edges in graph.values()),
            'weak_components': 1,
            'preprocessing_time_seconds': 0.1,
        },
        'artifact_size_bytes': graph_file.stat().st_size,
        'test_graph': True,
        'note': 'This is a synthetic test graph for development purposes only'
    }
    
    # Save metadata
    metadata_file = output_dir / 'harare_drive_graph_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Test graph created successfully!")
    logger.info(f"Graph file: {graph_file} ({graph_file.stat().st_size / 1024:.2f} KB)")
    logger.info(f"Metadata file: {metadata_file}")
    logger.info(f"Nodes: {len(nodes)}, Edges: {sum(len(edges) for edges in graph.values())}")
    logger.info("Note: This is a synthetic test graph. For production use, run the full OSM preprocessor.")


if __name__ == '__main__':
    create_test_graph()
