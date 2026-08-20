# Feature 6: Multi-Objective Route Optimization with Real Constraints

> **Priority:** 6 (Sixth to implement)  
> **Estimated Time:** 3-4 days  
> **Academic Value:** ⭐⭐⭐⭐⭐  
> **Complexity:** High  
> **Dependencies:** All previous features

---

## 🎯 Feature Overview

**What it adds:** Enhanced genetic algorithm that optimizes patrol routes for multiple real-world objectives simultaneously: fuel efficiency, risk coverage, officer safety, time windows, and road conditions.

**Academic Contribution:**
- Multi-objective optimization for law enforcement routing
- Real-world constraint satisfaction in route planning
- Pareto frontier analysis for trade-off visualization
- Advanced GA operators for complex optimization problems

**Operational Value:**
- Optimized routes that balance multiple operational priorities
- Explicit consideration of officer safety and wellbeing
- Time-aware routing for shift-based operations
- Road condition awareness for practical route planning

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│         Multi-Objective Route Optimization System         │
├─────────────────────────────────────────────────────────┤
│  1. Constraint Modeling System                         │
│     - Time windows (shift constraints, appointment times)│
│     - Safety constraints (avoid high-crime areas)         │
│     - Road conditions (traffic, construction, weather)   │
│     - Resource constraints (fuel, time, officer skills)  │
│                                                          │
│  2. Multi-Objective Fitness Function                    │
│     - Fuel efficiency optimization                       │
│     - Risk coverage maximization                        │
│     - Officer safety scoring                            │
│     - Time window compliance                             │
│     - Composite weighted objective function               │
│                                                          │
│  3. Enhanced Genetic Algorithm                           │
│     - Multi-objective NSGA-II implementation              │
│     - Advanced crossover operators                       │
│     - Adaptive mutation rates                           │
│     - Constraint handling mechanisms                     │
│                                                          │
│  4. Pareto Analysis & Visualization                    │
│     - Pareto frontier generation                        │
│     - Trade-off analysis between objectives             │
│     - Solution ranking and selection                    │
│     - Interactive visualization tools                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Multi-Objective Routing API                  │
│  POST /api/v1/routing/multi-optimize                    │
│  GET  /api/v1/routing/pareto-frontier                   │
│  POST /api/v1/routing/constraint-configuration           │
│  GET  /api/v1/routing/constraint-templates               │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Plan

### **Phase 1: Constraint Modeling (Day 1)**

#### 1.1 Create Constraint Model

**File:** `backend/app/services/advanced_routing/constraints.py`

```python
"""
Route Constraint Modeling
========================
Models real-world constraints for patrol route optimization.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np

from app.models.models import Incident, Hotspot


class ConstraintType(Enum):
    """Types of routing constraints."""
    TIME_WINDOW = "time_window"
    SAFETY = "safety"
    ROAD_CONDITION = "road_condition"
    RESOURCE = "resource"
    GEOGRAPHIC = "geographic"


class RouteConstraint:
    """
    Base class for routing constraints.
    
    Each constraint defines:
    - Applicability conditions
    - Penalty function for violations
    - Hard vs soft constraint classification
    - Constraint parameters
    """
    
    def __init__(
        self,
        constraint_type: ConstraintType,
        is_hard: bool = False,
        penalty_weight: float = 1.0
    ):
        self.constraint_type = constraint_type
        self.is_hard = is_hard  # Hard constraints cannot be violated
        self.penalty_weight = penalty_weight  # Weight for soft constraint violations
    
    def evaluate(self, route: List[Tuple[float, float]], context: Dict) -> Tuple[float, bool]:
        """
        Evaluate constraint on a route.
        
        Returns:
            (penalty_score, is_satisfied)
        """
        raise NotImplementedError("Subclasses must implement evaluate()")
    
    def apply_penalty(self, base_fitness: float, penalty: float) -> float:
        """Apply penalty to base fitness score."""
        if self.is_hard and penalty > 0:
            return float('inf')  # Hard constraint violations make solution invalid
        return base_fitness + (self.penalty_weight * penalty)


class TimeWindowConstraint(RouteConstraint):
    """
    Time window constraint for route optimization.
    
    Ensures route can be completed within available time windows
    (shift times, appointment times, etc.).
    """
    
    def __init__(
        self,
        start_time: datetime,
        end_time: datetime,
        service_time_per_stop: float = 15.0,  # minutes
        penalty_weight: float = 2.0
    ):
        super().__init__(ConstraintType.TIME_WINDOW, is_hard=True, penalty_weight=penalty_weight)
        self.start_time = start_time
        self.end_time = end_time
        self.service_time_per_stop = service_time_per_stop
        self.available_minutes = (end_time - start_time).total_seconds() / 60
    
    def evaluate(self, route: List[Tuple[float, float]], context: Dict) -> Tuple[float, bool]:
        """Evaluate if route can be completed within time window."""
        if len(route) < 2:
            return 0.0, True
        
        # Calculate total travel time (simplified)
        total_distance_km = self._calculate_total_distance(route)
        travel_time_minutes = total_distance_km * 2  # Assume 30 km/h average speed
        
        # Add service time for each stop
        total_service_time = len(route) * self.service_time_per_stop
        
        total_time = travel_time_minutes + total_service_time
        
        # Check if within time window
        is_satisfied = total_time <= self.available_minutes
        penalty = max(0, total_time - self.available_minutes) if not is_satisfied else 0.0
        
        return penalty, is_satisfied
    
    def _calculate_total_distance(self, route: List[Tuple[float, float]]) -> float:
        """Calculate total route distance."""
        total_distance = 0.0
        for i in range(len(route) - 1):
            total_distance += self._haversine_distance(
                route[i][0], route[i][1],
                route[i+1][0], route[i+1][1]
            )
        return total_distance
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance in kilometers."""
        import math
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c


class SafetyConstraint(RouteConstraint):
    """
    Safety constraint for route optimization.
    
    Penalizes routes that go through high-crime areas or dangerous locations.
    """
    
    def __init__(
        self,
        danger_zones: List[Dict],
        safety_radius_km: float = 1.0,
        penalty_weight: float = 3.0
    ):
        super().__init__(ConstraintType.SAFETY, is_hard=False, penalty_weight=penalty_weight)
        self.danger_zones = danger_zones  # List of {lat, lng, severity_multiplier}
        self.safety_radius_km = safety_radius_km
    
    def evaluate(self, route: List[Tuple[float, float]], context: Dict) -> Tuple[float, bool]:
        """Evaluate safety of route based on danger zones."""
        if not self.danger_zones:
            return 0.0, True
        
        total_penalty = 0.0
        route_violates = False
        
        for lat, lng in route:
            for zone in self.danger_zones:
                distance_km = self._haversine_distance(
                    lat, lng,
                    zone['lat'], zone['lng']
                )
                
                if distance_km <= self.safety_radius_km:
                    # Calculate penalty based on distance and zone severity
                    severity_multiplier = zone.get('severity_multiplier', 1.0)
                    distance_penalty = (self.safety_radius_km - distance_km) / self.safety_radius_km
                    zone_penalty = distance_penalty * severity_multiplier
                    total_penalty += zone_penalty
                    route_violates = True
        
        # Normalize penalty
        max_possible_penalty = len(route) * len(self.danger_zones)
        normalized_penalty = total_penalty / max_possible_penalty if max_possible_penalty > 0 else 0.0
        
        return normalized_penalty, not route_violates
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance in kilometers."""
        import math
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c


class RoadConditionConstraint(RouteConstraint):
    """
    Road condition constraint for route optimization.
    
    Accounts for traffic, construction, weather, and other road conditions.
    """
    
    def __init__(
        self,
        road_conditions: List[Dict],
        penalty_weight: float = 1.5
    ):
        super().__init__(ConstraintType.ROAD_CONDITION, is_hard=False, penalty_weight=penalty_weight)
        self.road_conditions = road_conditions  # List of {lat, lng, radius_km, speed_multiplier}
    
    def evaluate(self, route: List[Tuple[float, float]], context: Dict) -> Tuple[float, bool]:
        """Evaluate road condition impact on route."""
        if not self.road_conditions:
            return 0.0, True
        
        total_speed_impact = 0.0
        affected_segments = 0
        
        for i in range(len(route) - 1):
            segment_start = route[i]
            segment_end = route[i+1]
            
            segment_speed_impact = self._calculate_segment_speed_impact(
                segment_start, segment_end
            )
            
            if segment_speed_impact > 0:
                total_speed_impact += segment_speed_impact
                affected_segments += 1
        
        # Penalty based on overall speed reduction
        avg_speed_impact = total_speed_impact / max(len(route) - 1, 1)
        penalty = avg_speed_impact if avg_speed_impact > 0.3 else 0.0  # Only penalize significant impacts
        
        return penalty, penalty == 0.0
    
    def _calculate_segment_speed_impact(self, start: Tuple[float, float], end: Tuple[float, float]) -> float:
        """Calculate speed impact for a route segment."""
        max_impact = 0.0
        
        for condition in self.road_conditions:
            # Check if segment intersects with condition area
            if self._segment_intersects_condition(start, end, condition):
                speed_multiplier = condition.get('speed_multiplier', 1.0)
                if speed_multiplier < 1.0:
                    impact = 1.0 - speed_multiplier
                    max_impact = max(max_impact, impact)
        
        return max_impact
    
    def _segment_intersects_condition(self, start: Tuple[float, float], end: Tuple[float, float], condition: Dict) -> bool:
        """Check if route segment intersects with road condition area."""
        # Simplified: check if midpoint of segment is within condition radius
        mid_lat = (start[0] + end[0]) / 2
        mid_lng = (start[1] + end[1]) / 2
        
        distance_km = self._haversine_distance(
            mid_lat, mid_lng,
            condition['lat'], condition['lng']
        )
        
        return distance_km <= condition.get('radius_km', 0.5)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance in kilometers."""
        import math
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c


class ConstraintManager:
    """
    Manages multiple routing constraints and their evaluation.
    """
    
    def __init__(self):
        self.constraints: List[RouteConstraint] = []
    
    def add_constraint(self, constraint: RouteConstraint):
        """Add a constraint to the manager."""
        self.constraints.append(constraint)
    
    def evaluate_all_constraints(
        self, 
        route: List[Tuple[float, float]], 
        context: Dict
    ) -> Dict:
        """
        Evaluate all constraints on a route.
        
        Returns:
            Dict with total penalty, constraint breakdown, and validity
        """
        total_penalty = 0.0
        constraint_results = []
        is_valid = True
        
        for constraint in self.constraints:
            penalty, is_satisfied = constraint.evaluate(route, context)
            total_penalty += penalty
            
            constraint_results.append({
                'constraint_type': constraint.constraint_type.value,
                'penalty': penalty,
                'is_satisfied': is_satisfied,
                'is_hard': constraint.is_hard
            })
            
            if constraint.is_hard and not is_satisfied:
                is_valid = False
        
        return {
            'total_penalty': total_penalty,
            'constraint_results': constraint_results,
            'is_valid': is_valid
        }
    
    def apply_constraints_to_fitness(
        self, 
        base_fitness: float, 
        route: List[Tuple[float, float]], 
        context: Dict
    ) -> float:
        """Apply all constraints to base fitness score."""
        evaluation = self.evaluate_all_constraints(route, context)
        
        if not evaluation['is_valid']:
            return float('inf')  # Invalid solution
        
        adjusted_fitness = base_fitness + evaluation['total_penalty']
        return adjusted_fitness
```

---

### **Phase 2: Multi-Objective Fitness Function (Day 1-2)**

#### 2.1 Create Multi-Objective Fitness

**File:** `backend/app/services/advanced_routing/multi_objective_fitness.py`

```python
"""
Multi-Objective Fitness Function
================================
Optimizes routes for multiple objectives simultaneously.
"""
import numpy as np
from typing import List, Tuple, Dict
from geoalchemy2.shape import to_shape

from app.models.models import Hotspot
from app.services.advanced_routing.constraints import ConstraintManager


class MultiObjectiveFitness:
    """
    Multi-objective fitness function for patrol route optimization.
    
    Optimizes for:
    - Fuel efficiency (minimize distance)
    - Risk coverage (maximize hotspot coverage)
    - Officer safety (minimize danger zone exposure)
    - Time compliance (meet time windows)
    - Road conditions (avoid poor road conditions)
    """
    
    def __init__(self, constraint_manager: ConstraintManager):
        self.constraint_manager = constraint_manager
        
        # Objective weights (tunable for different priorities)
        self.objective_weights = {
            'fuel_efficiency': 0.3,      # Minimize distance
            'risk_coverage': 0.3,         # Maximize hotspot coverage
            'officer_safety': 0.2,        # Minimize danger zone exposure
            'time_compliance': 0.1,       # Meet time windows
            'road_conditions': 0.1         # Avoid poor road conditions
        }
        
        # Normalization factors
        self.max_distance_km = 50.0  # Maximum expected route distance
        self.max_risk_score = 1.0
    
    def calculate_fitness(
        self, 
        route: List[Tuple[float, float]], 
        context: Dict
    ) -> Dict:
        """
        Calculate multi-objective fitness for a route.
        
        Args:
            route: List of (lat, lng) tuples representing the route
            context: Dict with hotspots, constraints, and other context
            
        Returns:
            Dict with individual objective scores and composite fitness
        """
        if len(route) < 2:
            return {
                'fuel_efficiency': 1.0,
                'risk_coverage': 0.0,
                'officer_safety': 1.0,
                'time_compliance': 1.0,
                'road_conditions': 1.0,
                'composite_fitness': float('inf'),
                'is_valid': False
            }
        
        # Calculate individual objectives
        fuel_score = self._calculate_fuel_efficiency(route)
        risk_score = self._calculate_risk_coverage(route, context.get('hotspots', []))
        safety_score = self._calculate_officer_safety(route, context.get('danger_zones', []))
        time_score = self._calculate_time_compliance(route, context)
        road_score = self._calculate_road_conditions(route, context.get('road_conditions', []))
        
        # Calculate composite fitness (weighted sum)
        composite_fitness = (
            self.objective_weights['fuel_efficiency'] * fuel_score +
            self.objective_weights['risk_coverage'] * (1.0 - risk_score) +  # Maximize coverage
            self.objective_weights['officer_safety'] * safety_score +
            self.objective_weights['time_compliance'] * time_score +
            self.objective_weights['road_conditions'] * road_score
        )
        
        # Apply constraints
        constrained_fitness = self.constraint_manager.apply_constraints_to_fitness(
            composite_fitness, route, context
        )
        
        return {
            'fuel_efficiency': fuel_score,
            'risk_coverage': risk_score,
            'officer_safety': safety_score,
            'time_compliance': time_score,
            'road_conditions': road_score,
            'composite_fitness': constrained_fitness,
            'is_valid': constrained_fitness != float('inf')
        }
    
    def _calculate_fuel_efficiency(self, route: List[Tuple[float, float]]) -> float:
        """Calculate fuel efficiency score (lower distance = better)."""
        total_distance = self._calculate_total_distance(route)
        normalized_distance = total_distance / self.max_distance_km
        return normalized_distance  # Lower is better
    
    def _calculate_risk_coverage(self, route: List[Tuple[float, float]], hotspots: List) -> float:
        """Calculate risk coverage score (higher coverage = better)."""
        if not hotspots:
            return 0.0
        
        covered_hotspots = 0
        coverage_radius_km = 1.0  # Routes cover hotspots within 1km
        
        for hotspot in hotspots:
            if not hotspot.centroid:
                continue
            
            centroid_point = to_shape(hotspot.centroid)
            
            # Check if any route point is near this hotspot
            for lat, lng in route:
                distance_km = self._haversine_distance(
                    lat, lng,
                    centroid_point.y, centroid_point.x
                )
                
                if distance_km <= coverage_radius_km:
                    covered_hotspots += 1
                    break
        
        coverage_ratio = covered_hotspots / len(hotspots)
        return coverage_ratio
    
    def _calculate_officer_safety(self, route: List[Tuple[float, float]], danger_zones: List[Dict]) -> float:
        """Calculate officer safety score (lower danger exposure = better)."""
        if not danger_zones:
            return 1.0  # Perfect safety if no danger zones
        
        danger_exposure = 0.0
        safety_radius_km = 0.5  # Consider danger exposure within 500m
        
        for lat, lng in route:
            for zone in danger_zones:
                distance_km = self._haversine_distance(
                    lat, lng,
                    zone['lat'], zone['lng']
                )
                
                if distance_km <= safety_radius_km:
                    severity_multiplier = zone.get('severity_multiplier', 1.0)
                    danger_exposure += severity_multiplier
        
        # Normalize exposure
        max_possible_exposure = len(route) * len(danger_zones)
        normalized_exposure = danger_exposure / max_possible_exposure if max_possible_exposure > 0 else 0.0
        
        # Safety score is inverse of exposure
        safety_score = 1.0 - normalized_exposure
        return max(0.0, safety_score)
    
    def _calculate_time_compliance(self, route: List[Tuple[float, float]], context: Dict) -> float:
        """Calculate time compliance score."""
        time_window = context.get('time_window')
        if not time_window:
            return 1.0  # Perfect compliance if no time window constraint
        
        # Simplified time calculation
        total_distance = self._calculate_total_distance(route)
        travel_time_hours = total_distance / 30.0  # Assume 30 km/h average
        service_time_hours = len(route) * 0.25  # 15 minutes per stop
        
        total_time_hours = travel_time_hours + service_time_hours
        available_hours = (time_window['end'] - time_window['start']).total_seconds() / 3600
        
        if total_time_hours <= available_hours:
            return 1.0  # Perfect compliance
        
        # Penalty for overtime
        overtime_ratio = (total_time_hours - available_hours) / available_hours
        compliance_score = max(0.0, 1.0 - overtime_ratio)
        return compliance_score
    
    def _calculate_road_conditions(self, route: List[Tuple[float, float]], road_conditions: List[Dict]) -> float:
        """Calculate road conditions score."""
        if not road_conditions:
            return 1.0  # Perfect conditions if no road issues
        
        total_impact = 0.0
        affected_segments = 0
        
        for i in range(len(route) - 1):
            segment_start = route[i]
            segment_end = route[i+1]
            
            for condition in road_conditions:
                if self._segment_intersects_condition(segment_start, segment_end, condition):
                    speed_multiplier = condition.get('speed_multiplier', 1.0)
                    if speed_multiplier < 1.0:
                        impact = 1.0 - speed_multiplier
                        total_impact += impact
                        affected_segments += 1
                        break
        
        # Normalize impact
        max_possible_impact = len(route) - 1
        normalized_impact = total_impact / max_possible_impact if max_possible_impact > 0 else 0.0
        
        # Road score is inverse of impact
        road_score = 1.0 - normalized_impact
        return max(0.0, road_score)
    
    def _calculate_total_distance(self, route: List[Tuple[float, float]]) -> float:
        """Calculate total route distance."""
        total_distance = 0.0
        for i in range(len(route) - 1):
            total_distance += self._haversine_distance(
                route[i][0], route[i][1],
                route[i+1][0], route[i+1][1]
            )
        return total_distance
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance in kilometers."""
        import math
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    def _segment_intersects_condition(self, start: Tuple[float, float], end: Tuple[float, float], condition: Dict) -> bool:
        """Check if route segment intersects with road condition area."""
        mid_lat = (start[0] + end[0]) / 2
        mid_lng = (start[1] + end[1]) / 2
        
        distance_km = self._haversine_distance(
            mid_lat, mid_lng,
            condition['lat'], condition['lng']
        )
        
        return distance_km <= condition.get('radius_km', 0.5)
```

---

### **Phase 3: Enhanced Genetic Algorithm (Day 2-3)**

#### 3.1 Create Enhanced GA Solver

**File:** `backend/app/services/advanced_routing/enhanced_ga.py`

```python
"""
Enhanced Genetic Algorithm for Multi-Objective Routing
=====================================================
NSGA-II inspired algorithm for multi-objective route optimization.
"""
import numpy as np
import random
from typing import List, Tuple, Dict, Optional
from datetime import datetime

from app.services.advanced_routing.multi_objective_fitness import MultiObjectiveFitness
from app.services.advanced_routing.constraints import ConstraintManager


class EnhancedGeneticSolver:
    """
    Enhanced genetic algorithm for multi-objective route optimization.
    
    Features:
    - Multi-objective optimization (NSGA-II inspired)
    - Advanced crossover operators
    - Adaptive mutation rates
    - Constraint handling mechanisms
    - Pareto frontier maintenance
    """
    
    def __init__(
        self,
        waypoints: List[Tuple[float, float]],
        constraint_manager: ConstraintManager,
        pop_size: int = 100,
        generations: int = 200,
        mutation_rate: float = 0.02,
        crossover_rate: float = 0.8,
        tournament_size: int = 3
    ):
        self.waypoints = waypoints
        self.constraint_manager = constraint_manager
        self.fitness_calculator = MultiObjectiveFitness(constraint_manager)
        
        # GA parameters
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        
        # Tracking
        self.fitness_history = []
        self.pareto_frontier = []
        self.convergence_data = []
    
    def solve(self, context: Dict) -> Tuple[List[Tuple[float, float]], Dict]:
        """
        Solve the multi-objective routing problem.
        
        Args:
            context: Dict with hotspots, constraints, and other context
            
        Returns:
            (best_route, analysis_results)
        """
        # Initialize population
        population = self._initialize_population()
        
        # Evaluate initial population
        evaluated_population = self._evaluate_population(population, context)
        
        # Evolution loop
        for generation in range(self.generations):
            # Selection
            selected = self._selection(evaluated_population)
            
            # Crossover
            offspring = self._crossover(selected)
            
            # Mutation
            mutated = self._mutation(offspring)
            
            # Evaluate offspring
            evaluated_offspring = self._evaluate_population(mutated, context)
            
            # Combine and select next generation
            combined = evaluated_population + evaluated_offspring
            next_generation = self._environmental_selection(combined)
            
            # Update population
            evaluated_population = next_generation
            
            # Track fitness
            best_fitness = min(ind['fitness'] for ind in evaluated_population)
            self.fitness_history.append(best_fitness)
            
            # Update Pareto frontier
            self._update_pareto_frontier(evaluated_population)
        
        # Select best solution from Pareto frontier
        best_solution = self._select_best_from_pareto(context)
        
        analysis_results = {
            'fitness_history': self.fitness_history,
            'pareto_frontier_size': len(self.pareto_frontier),
            'generations': self.generations,
            'final_fitness': best_solution['fitness'],
            'objective_scores': best_solution['objectives']
        }
        
        return best_solution['route'], analysis_results
    
    def _initialize_population(self) -> List[List[Tuple[float, float]]]:
        """Initialize random population."""
        population = []
        
        for _ in range(self.pop_size):
            # Random permutation of waypoints
            shuffled_waypoints = self.waypoints.copy()
            random.shuffle(shuffled_waypoints)
            
            # Optionally return to start
            if random.random() > 0.5:
                shuffled_waypoints.append(shuffled_waypoints[0])
            
            population.append(shuffled_waypoints)
        
        return population
    
    def _evaluate_population(self, population: List[List[Tuple[float, float]]], context: Dict) -> List[Dict]:
        """Evaluate fitness for entire population."""
        evaluated = []
        
        for route in population:
            fitness_data = self.fitness_calculator.calculate_fitness(route, context)
            
            evaluated.append({
                'route': route,
                'fitness': fitness_data['composite_fitness'],
                'objectives': {
                    'fuel_efficiency': fitness_data['fuel_efficiency'],
                    'risk_coverage': fitness_data['risk_coverage'],
                    'officer_safety': fitness_data['officer_safety'],
                    'time_compliance': fitness_data['time_compliance'],
                    'road_conditions': fitness_data['road_conditions']
                },
                'is_valid': fitness_data['is_valid']
            })
        
        return evaluated
    
    def _selection(self, population: List[Dict]) -> List[Dict]:
        """Tournament selection."""
        selected = []
        
        for _ in range(len(population)):
            # Select tournament participants
            tournament = random.sample(population, min(self.tournament_size, len(population)))
            
            # Select winner (lowest fitness)
            winner = min(tournament, key=lambda x: x['fitness'] if x['is_valid'] else float('inf'))
            selected.append(winner)
        
        return selected
    
    def _crossover(self, population: List[Dict]) -> List[List[Tuple[float, float]]]:
        """Ordered crossover (OX) for route optimization."""
        offspring = []
        
        for i in range(0, len(population), 2):
            if i + 1 >= len(population):
                # Odd individual, just copy
                offspring.append(population[i]['route'])
                continue
            
            parent1 = population[i]['route']
            parent2 = population[i+1]['route']
            
            if random.random() < self.crossover_rate:
                child1, child2 = self._ordered_crossover(parent1, parent2)
                offspring.extend([child1, child2])
            else:
                offspring.extend([parent1, parent2])
        
        return offspring
    
    def _ordered_crossover(self, parent1: List, parent2: List) -> Tuple[List, List]:
        """Ordered crossover operator for permutation encoding."""
        if len(parent1) < 3:
            return parent1.copy(), parent2.copy()
        
        # Select random crossover points
        start = random.randint(0, len(parent1) - 2)
        end = random.randint(start + 1, len(parent1) - 1)
        
        # Create children
        child1 = [None] * len(parent1)
        child2 = [None] * len(parent2)
        
        # Copy segment from parents
        child1[start:end] = parent1[start:end]
        child2[start:end] = parent2[start:end]
        
        # Fill remaining positions with order from other parent
        self._fill_crossover_child(child1, parent2, start, end)
        self._fill_crossover_child(child2, parent1, start, end)
        
        return child1, child2
    
    def _fill_crossover_child(self, child: List, other_parent: List, start: int, end: int):
        """Fill remaining positions in crossover child."""
        current_pos = end % len(child)
        
        for item in other_parent:
            if item not in child:
                child[current_pos] = item
                current_pos = (current_pos + 1) % len(child)
    
    def _mutation(self, population: List[List[Tuple[float, float]]]) -> List[List[Tuple[float, float]]]:
        """Mutation with adaptive rate."""
        mutated = []
        
        for route in population:
            if random.random() < self.mutation_rate:
                mutated_route = self._mutate_route(route)
                mutated.append(mutated_route)
            else:
                mutated.append(route)
        
        return mutated
    
    def _mutate_route(self, route: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Apply mutation to a route."""
        if len(route) < 3:
            return route.copy()
        
        mutation_type = random.choice(['swap', 'inversion', 'insertion'])
        
        if mutation_type == 'swap':
            return self._swap_mutation(route)
        elif mutation_type == 'inversion':
            return self._inversion_mutation(route)
        else:
            return self._insertion_mutation(route)
    
    def _swap_mutation(self, route: List) -> List:
        """Swap two random positions."""
        mutated = route.copy()
        i, j = random.sample(range(len(mutated)), 2)
        mutated[i], mutated[j] = mutated[j], mutated[i]
        return mutated
    
    def _inversion_mutation(self, route: List) -> List:
        """Invert a random segment."""
        mutated = route.copy()
        i, j = sorted(random.sample(range(len(mutated)), 2))
        mutated[i:j+1] = mutated[i:j+1][::-1]
        return mutated
    
    def _insertion_mutation(self, route: List) -> List:
        """Move a random element to another position."""
        mutated = route.copy()
        i, j = random.sample(range(len(mutated)), 2)
        element = mutated.pop(i)
        mutated.insert(j, element)
        return mutated
    
    def _environmental_selection(self, population: List[Dict]) -> List[Dict]:
        """Select next generation using Pareto dominance."""
        # Sort by fitness (simple approach for now)
        # Full NSGA-II would use non-dominated sorting
        sorted_pop = sorted(population, key=lambda x: x['fitness'] if x['is_valid'] else float('inf'))
        
        # Select top individuals
        return sorted_pop[:self.pop_size]
    
    def _update_pareto_frontier(self, population: List[Dict]):
        """Update Pareto frontier with non-dominated solutions."""
        # Filter valid solutions
        valid_solutions = [ind for ind in population if ind['is_valid']]
        
        # Simple Pareto filtering (full NSGA-II would be more sophisticated)
        for candidate in valid_solutions:
            is_dominated = False
            
            for existing in self.pareto_frontier:
                if self._dominates(existing, candidate):
                    is_dominated = True
                    break
                elif self._dominates(candidate, existing):
                    self.pareto_frontier.remove(existing)
            
            if not is_dominated:
                self.pareto_frontier.append(candidate)
    
    def _dominates(self, solution1: Dict, solution2: Dict) -> bool:
        """Check if solution1 dominates solution2 (minimization)."""
        obj1 = solution1['objectives']
        obj2 = solution2['objectives']
        
        # Solution1 dominates if it's better or equal in all objectives
        # and strictly better in at least one
        at_least_one_better = False
        
        for obj_name in obj1:
            if obj1[obj_name] > obj2[obj_name]:  # Higher is worse for minimization
                return False
            elif obj1[obj_name] < obj2[obj_name]:
                at_least_one_better = True
        
        return at_least_one_better
    
    def _select_best_from_pareto(self, context: Dict) -> Dict:
        """Select best solution from Pareto frontier based on context preferences."""
        if not self.pareto_frontier:
            # Fallback to population best
            return min(self.fitness_history, key=lambda x: x)
        
        # Weighted selection based on objective weights
        weighted_scores = []
        
        for solution in self.pareto_frontier:
            objectives = solution['objectives']
            weights = self.fitness_calculator.objective_weights
            
            # Calculate weighted score (normalize objectives)
            score = (
                weights['fuel_efficiency'] * objectives['fuel_efficiency'] +
                weights['risk_coverage'] * (1.0 - objectives['risk_coverage']) +
                weights['officer_safety'] * objectives['officer_safety'] +
                weights['time_compliance'] * objectives['time_compliance'] +
                weights['road_conditions'] * objectives['road_conditions']
            )
            
            weighted_scores.append((score, solution))
        
        # Select best weighted score
        best_score, best_solution = min(weighted_scores, key=lambda x: x[0])
        
        return best_solution
```

---

### **Phase 4: API Integration (Day 3-4)**

#### 4.1 Create Multi-Objective Routing API

**File:** `backend/app/api/v1/routes/multi_objective_routing.py`

```python
"""
Multi-Objective Routing API Routes
=================================
Endpoints for advanced multi-objective route optimization.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app import db
from app.models.models import Hotspot
from app.services.advanced_routing.constraints import (
    ConstraintManager,
    TimeWindowConstraint,
    SafetyConstraint,
    RoadConditionConstraint
)
from app.services.advanced_routing.enhanced_ga import EnhancedGeneticSolver

multi_objective_bp = Blueprint("multi_objective", __name__)


@multi_objective_bp.post("/optimize")
@jwt_required()
def optimize_multi_objective():
    """
    Optimize route using multi-objective genetic algorithm.
    
    Request: {
        "waypoints": [{"lat": float, "lng": float}, ...],
        "constraints": {
            "time_window": {"start": str, "end": str},
            "danger_zones": [{"lat": float, "lng": float, "severity_multiplier": float}, ...],
            "road_conditions": [{"lat": float, "lng": float, "radius_km": float, "speed_multiplier": float}, ...]
        },
        "objectives": {
            "fuel_efficiency_weight": float,
            "risk_coverage_weight": float,
            "officer_safety_weight": float,
            "time_compliance_weight": float,
            "road_conditions_weight": float
        },
        "ga_config": {
            "pop_size": int,
            "generations": int,
            "mutation_rate": float,
            "crossover_rate": float
        }
    }
    """
    data = request.get_json()
    
    waypoints = [(wp['lat'], wp['lng']) for wp in data.get('waypoints', [])]
    constraints_config = data.get('constraints', {})
    objectives_config = data.get('objectives', {})
    ga_config = data.get('ga_config', {})
    
    if len(waypoints) < 2:
        return jsonify({'error': 'At least 2 waypoints required'}), 400
    
    try:
        # Setup constraint manager
        constraint_manager = ConstraintManager()
        
        # Add time window constraint if provided
        if 'time_window' in constraints_config:
            time_window = constraints_config['time_window']
            start_time = datetime.fromisoformat(time_window['start'])
            end_time = datetime.fromisoformat(time_window['end'])
            constraint_manager.add_constraint(
                TimeWindowConstraint(start_time, end_time)
            )
        
        # Add safety constraints if provided
        if 'danger_zones' in constraints_config:
            constraint_manager.add_constraint(
                SafetyConstraint(constraints_config['danger_zones'])
            )
        
        # Add road condition constraints if provided
        if 'road_conditions' in constraints_config:
            constraint_manager.add_constraint(
                RoadConditionConstraint(constraints_config['road_conditions'])
            )
        
        # Get hotspots for risk coverage
        hotspots = Hotspot.query.filter(
            Hotspot.risk_score >= 0.5
        ).all()
        
        # Setup context
        context = {
            'hotspots': hotspots,
            'time_window': constraints_config.get('time_window'),
            'danger_zones': constraints_config.get('danger_zones', []),
            'road_conditions': constraints_config.get('road_conditions', [])
        }
        
        # Create solver with custom config
        solver = EnhancedGeneticSolver(
            waypoints=waypoints,
            constraint_manager=constraint_manager,
            pop_size=ga_config.get('pop_size', 100),
            generations=ga_config.get('generations', 200),
            mutation_rate=ga_config.get('mutation_rate', 0.02),
            crossover_rate=ga_config.get('crossover_rate', 0.8)
        )
        
        # Customize objective weights if provided
        if objectives_config:
            solver.fitness_calculator.objective_weights.update(objectives_config)
        
        # Solve
        best_route, analysis = solver.solve(context)
        
        return jsonify({
            'optimized_route': best_route,
            'analysis': analysis,
            'objective_scores': analysis['objective_scores'],
            'constraints_applied': len(constraint_manager.constraints),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@multi_objective_bp.get("/pareto-frontier")
@jwt_required()
def get_pareto_frontier():
    """
    Get Pareto frontier from last optimization run.
    
    Response: { "pareto_solutions": [...], "frontier_analysis": {...} }
    """
    # This would require storing the last Pareto frontier
    # For now, return placeholder response
    return jsonify({
        'pareto_solutions': [],
        'frontier_analysis': {
            'frontier_size': 0,
            'objective_ranges': {},
            'trade_off_analysis': {}
        },
        'message': 'Pareto frontier requires solver state persistence'
    }), 200


@multi_objective_bp.post("/constraint-configuration")
@jwt_required()
def save_constraint_template():
    """
    Save a constraint configuration template for reuse.
    
    Request: { "name": str, "constraints": {...}, "objectives": {...} }
    Response: { "template_id": str, "saved_at": str }
    """
    data = request.get_json()
    name = data.get('name')
    constraints = data.get('constraints')
    objectives = data.get('objectives')
    
    # This would require a ConstraintTemplate model
    # For now, return success response
    template_id = hash(f"{name}_{datetime.utcnow()}")
    
    return jsonify({
        'template_id': str(template_id),
        'name': name,
        'saved_at': datetime.utcnow().isoformat()
    }), 201


@multi_objective_bp.get("/constraint-templates")
@jwt_required()
def get_constraint_templates():
    """
    Get available constraint configuration templates.
    
    Response: { "templates": [...] }
    """
    # This would require ConstraintTemplate model
    # Return some example templates
    example_templates = [
        {
            'id': 'day_shift_standard',
            'name': 'Standard Day Shift',
            'description': 'Standard patrol constraints for day shift operations',
            'constraints': {
                'time_window': {
                    'start': '08:00',
                    'end': '17:00'
                }
            },
            'objectives': {
                'fuel_efficiency_weight': 0.4,
                'risk_coverage_weight': 0.3,
                'officer_safety_weight': 0.2,
                'time_compliance_weight': 0.1,
                'road_conditions_weight': 0.0
            }
        },
        {
            'id': 'night_shift_emphasis',
            'name': 'Night Shift Safety Emphasis',
            'description': 'Higher priority on officer safety for night operations',
            'objectives': {
                'fuel_efficiency_weight': 0.2,
                'risk_coverage_weight': 0.2,
                'officer_safety_weight': 0.5,
                'time_compliance_weight': 0.1,
                'road_conditions_weight': 0.0
            }
        }
    ]
    
    return jsonify({'templates': example_templates}), 200
```

#### 4.2 Register Multi-Objective Blueprint

**File:** `backend/app/__init__.py`

```python
# Add to existing imports
from app.api.v1.routes.multi_objective_routing import multi_objective_bp

# Add to blueprint registration
app.register_blueprint(multi_objective_bp, url_prefix="/api/v1/routing")
```

---

## 📊 Academic Evaluation Framework

### **Research Questions:**
1. How does multi-objective optimization compare to single-objective approaches?
2. What are the trade-offs between different objectives in patrol routing?
3. How do real-world constraints affect route optimization quality?

### **Evaluation Metrics:**
- **Pareto Frontier Quality:** Number and diversity of non-dominated solutions
- **Convergence Speed:** Generations needed to reach stable Pareto frontier
- **Constraint Satisfaction:** Percentage of solutions meeting all constraints
- **Objective Trade-offs:** Analysis of how objectives interact

### **Success Criteria:**
- Pareto frontier contains ≥10 non-dominated solutions
- Convergence achieved within 150 generations
- ≥80% of solutions meet all hard constraints
- Clear trade-off patterns visible between objectives

---

## 🎯 Acceptance Checklist

### **Backend Requirements:**
- ✅ Constraint system models real-world constraints
- ✅ Multi-objective fitness function works correctly
- ✅ Enhanced GA implements NSGA-II concepts
- ✅ Pareto frontier maintained during evolution
- ✅ API endpoints provide multi-objective optimization

### **Frontend Requirements:**
- ✅ Constraint configuration interface
- ✅ Objective weight adjustment controls
- ✅ Pareto frontier visualization
- ✅ Trade-off analysis display

### **Testing Requirements:**
- ✅ Unit tests for constraint evaluation
- ✅ Multi-objective fitness function tests
- ✅ GA convergence analysis
- ✅ Constraint satisfaction validation

### **Academic Requirements:**
- ✅ Multi-objective optimization methodology documented
- ✅ Constraint modeling approach explained
- ✅ Pareto analysis methodology described
- ✅ Trade-off analysis results presented

---

## 🚀 Implementation Complete

After completing Multi-Objective Route Optimization:

1. **All Features Implemented:** All 6 enhancement features are now complete
2. **Documentation:** Update dissertation with multi-objective optimization results
3. **Integration:** Test all features working together
4. **Final Evaluation:** Run comprehensive system evaluation

---

## 📝 Notes for Dissertation

### **Chapter 3 - Methodology Additions:**
- **Section 3.X: Multi-Objective Optimization Methodology**
  - Constraint modeling approach and rationale
  - Multi-objective fitness function design
  - Enhanced genetic algorithm implementation details
  - Pareto frontier analysis methodology

### **Chapter 4 - Results Additions:**
- **Section 4.X: Multi-Objective Optimization Results**
  - Pareto frontier visualization and analysis
  - Objective trade-off analysis
  - Constraint satisfaction performance
  - Comparison with single-objective approaches

### **Academic Contributions:**
- Novel multi-objective optimization for law enforcement routing
- Comprehensive constraint modeling framework
- NSGA-II adaptation for patrol route optimization
- Quantitative trade-off analysis for operational decisions

This feature represents the culmination of the enhancement work, providing the most sophisticated optimization capabilities while being implementable within 3-4 days.
