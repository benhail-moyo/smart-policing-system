"""
Routing system configuration.
Contains settings for road network routing algorithms and parameters.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RoutingConfig:
    """Configuration for road network routing system."""
    
    # Graph settings
    graph_path: str = 'ml/routing/data/harare_drive_graph.json.gz'
    metadata_path: str = 'ml/routing/data/harare_drive_graph_metadata.json'
    city: str = 'harare'
    
    # Spatial index settings
    max_snap_distance_m: float = 2000.0  # Maximum distance for snapping points to graph (2km)
    
    # Genetic Algorithm defaults
    ga_population_size: int = 100
    ga_generations: int = 200
    ga_mutation_rate: float = 0.02
    ga_crossover_rate: float = 0.8
    ga_tournament_size: int = 3
    ga_elitism_count: int = 2
    
    # GA parameter bounds (server-side limits)
    ga_min_population_size: int = 10
    ga_max_population_size: int = 500
    ga_min_generations: int = 10
    ga_max_generations: int = 500
    ga_min_mutation_rate: float = 0.001
    ga_max_mutation_rate: float = 0.5
    ga_min_crossover_rate: float = 0.1
    ga_max_crossover_rate: float = 1.0
    
    # Fuel consumption model (for estimates)
    fuel_consumption_l_per_km_urban: float = 0.15  # 15L/100km for urban patrol
    fuel_consumption_l_per_km_highway: float = 0.10  # 10L/100km for highway
    average_speed_kmh: float = 40.0  # Average urban patrol speed
    
    # Performance thresholds
    max_graph_load_time_seconds: float = 30.0
    max_route_query_time_ms: float = 5000.0
    max_memory_mb: int = 600
    
    # Harare bounding box (for validation)
    harare_bounds = {
        'north': -17.7,
        'south': -17.9,
        'east': 31.2,
        'west': 31.0
    }


# Global configuration instance
routing_config = RoutingConfig()
