"""
Graph store for loading and managing the immutable road network graph.
Loads the graph once per Flask worker and provides thread-safe access.
"""
import gzip
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GraphMetadata:
    """Metadata about the loaded road network graph."""
    city: str
    nodes: int
    directed_edges: int
    artifact_version: str
    memory_bytes: int
    load_time_ms: float
    osm_source_url: Optional[str] = None
    crop_bounds: Optional[Dict[str, float]] = None
    preprocessing_date: Optional[str] = None


@dataclass
class GraphState:
    """Current state of the graph store."""
    state: str  # 'not_loaded', 'loading', 'ready', 'failed'
    metadata: Optional[GraphMetadata] = None
    error: Optional[str] = None


class GraphStore:
    """
    Thread-safe singleton for loading and storing the road network graph.
    Uses adjacency list representation: dict[node_id, list[edge_dict]]
    """
    
    _instance: Optional['GraphStore'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure one graph instance per process."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize graph store (only runs once due to singleton)."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._graph: Dict[int, List[Dict]] = {}
        self._nodes: Dict[int, Dict[str, float]] = {}  # node_id -> {lat, lng}
        self._metadata: Optional[GraphMetadata] = None
        self._state = GraphState(state='not_loaded')
        self._load_lock = threading.Lock()
        
        # Default graph path
        self.graph_path = Path(__file__).parent.parent.parent.parent / 'ml' / 'routing' / 'data' / 'harare_drive_graph.json.gz'
        self.metadata_path = Path(__file__).parent.parent.parent.parent / 'ml' / 'routing' / 'data' / 'harare_drive_graph_metadata.json'
    
    def get_graph(self) -> tuple[Dict[int, List[Dict]], Dict[int, Dict[str, float]]]:
        """
        Get the loaded graph and nodes.
        Returns (graph, nodes) where graph is adjacency list and nodes is node_id -> {lat, lng}.
        
        Returns:
            Tuple of (graph adjacency list, nodes dict)
        
        Raises:
            RuntimeError: If graph is not ready or failed to load
        """
        if self._state.state == 'not_loaded':
            self._load_graph()
        elif self._state.state == 'loading':
            # Wait for loading to complete (with timeout)
            timeout = 30  # seconds
            start = time.time()
            while self._state.state == 'loading' and (time.time() - start) < timeout:
                time.sleep(0.1)
            
            if self._state.state == 'loading':
                raise RuntimeError("Graph loading timeout")
        
        if self._state.state != 'ready':
            raise RuntimeError(f"Graph not ready: {self._state.state} - {self._state.error}")
        
        return self._graph, self._nodes
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current graph status and metadata.
        
        Returns:
            Dict with state, city, nodes, directed_edges, artifact_version, memory_bytes
        """
        if self._state.state == 'ready' and self._metadata:
            return {
                'state': self._state.state,
                'city': self._metadata.city,
                'nodes': self._metadata.nodes,
                'directed_edges': self._metadata.directed_edges,
                'artifact_version': self._metadata.artifact_version,
                'memory_bytes': self._metadata.memory_bytes,
            }
        else:
            return {
                'state': self._state.state,
                'city': None,
                'nodes': 0,
                'directed_edges': 0,
                'artifact_version': None,
                'memory_bytes': 0,
            }
    
    def reset(self):
        """
        Reset the graph store (test-only hook).
        Clears loaded graph and returns to not_loaded state.
        """
        with self._load_lock:
            self._graph = {}
            self._nodes = {}
            self._metadata = None
            self._state = GraphState(state='not_loaded')
            logger.info("Graph store reset")
    
    def _load_graph(self):
        """
        Load the graph from disk with thread-safe initialization.
        Only one thread performs the actual loading; others wait.
        """
        with self._load_lock:
            # Double-check pattern
            if self._state.state == 'ready':
                return
            
            if self._state.state == 'loading':
                # Another thread is loading, wait for it
                return
            
            self._state = GraphState(state='loading')
            start_time = time.perf_counter()
            
            try:
                logger.info(f"Loading graph from {self.graph_path}")
                
                if not self.graph_path.exists():
                    raise FileNotFoundError(f"Graph file not found: {self.graph_path}")
                
                # Load graph data
                with gzip.open(self.graph_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Parse graph structure
                self._graph = {int(k): v for k, v in data.get('graph', {}).items()}
                self._nodes = {int(k): v for k, v in data.get('nodes', {}).items()}
                
                # Load metadata if available
                metadata_data = {}
                if self.metadata_path.exists():
                    with open(self.metadata_path, 'r', encoding='utf-8') as f:
                        metadata_data = json.load(f)
                
                # Calculate memory usage (approximate)
                import sys
                graph_size = sys.getsizeof(self._graph) + sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in self._graph.items())
                nodes_size = sys.getsizeof(self._nodes) + sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in self._nodes.items())
                total_memory = graph_size + nodes_size
                
                load_time_ms = (time.perf_counter() - start_time) * 1000
                
                self._metadata = GraphMetadata(
                    city=metadata_data.get('city', 'harare'),
                    nodes=len(self._nodes),
                    directed_edges=sum(len(edges) for edges in self._graph.values()),
                    artifact_version=metadata_data.get('version', 'unknown'),
                    memory_bytes=total_memory,
                    load_time_ms=load_time_ms,
                    osm_source_url=metadata_data.get('osm_source_url'),
                    crop_bounds=metadata_data.get('crop_bounds'),
                    preprocessing_date=metadata_data.get('preprocessing_date'),
                )
                
                self._state = GraphState(state='ready', metadata=self._metadata)
                
                logger.info(
                    f"Graph loaded successfully: {self._metadata.nodes} nodes, "
                    f"{self._metadata.directed_edges} directed edges, "
                    f"{self._metadata.memory_bytes / 1024 / 1024:.2f} MB, "
                    f"load time: {self._metadata.load_time_ms:.2f} ms"
                )
                
            except Exception as e:
                self._state = GraphState(state='failed', error=str(e))
                logger.error(f"Failed to load graph: {e}", exc_info=True)
                raise


# Global instance
graph_store = GraphStore()
