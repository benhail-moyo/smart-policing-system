"""
Manual Genetic Algorithm implementation for multi-stop patrol route optimization.
This is a clean-room implementation without DEAP operators for dissertation requirements.
"""
import random
import time
import copy
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class GAConfig:
    """Configuration parameters for the Genetic Algorithm."""
    population_size: int = 100
    generations: int = 200
    mutation_rate: float = 0.02
    crossover_rate: float = 0.8
    tournament_size: int = 3
    elitism_count: int = 2
    seed: Optional[int] = None


@dataclass
class GAResult:
    """Result of Genetic Algorithm optimization."""
    best_order: List[int]  # Ordered indices of stops (0 = start, fixed)
    best_distance: float  # Total distance of best route
    seed_used: int  # Random seed used for reproducibility
    generations_completed: int
    convergence_history: List[float]  # Fitness values per generation
    execution_time_ms: float


class GeneticAlgorithm:
    """
    Manual Genetic Algorithm for the Traveling Salesman Problem variant.
    
    The first waypoint (depot/start) is kept fixed; the algorithm evolves
    permutations of the remaining stops. Uses tournament selection, Ordered Crossover,
    swap/inversion mutation, and elitism.
    """
    
    def __init__(self, distance_matrix: List[List[float]], config: GAConfig):
        """
        Initialize GA with a precomputed distance matrix.
        
        Args:
            distance_matrix: N x N matrix where distance_matrix[i][j] is distance from i to j
                            Index 0 is assumed to be the fixed start point
            config: GA configuration parameters
        """
        self.distance_matrix = distance_matrix
        self.config = config
        self.num_stops = len(distance_matrix)
        
        if self.config.seed is not None:
            random.seed(self.config.seed)
        
        # Validate matrix
        if self.num_stops < 2:
            raise ValueError("Distance matrix must have at least 2 points")
        
        # Track convergence
        self.convergence_history: List[float] = []
        self.best_individual: Optional[List[int]] = None
        self.best_fitness: float = float('inf')
    
    def solve(self) -> GAResult:
        """
        Run the genetic algorithm to find an optimal route ordering.
        
        Returns:
            GAResult with best ordering and performance metrics
        """
        start_time = time.perf_counter()
        
        # Handle trivial cases
        if self.num_stops == 2:
            return GAResult(
                best_order=[0, 1],
                best_distance=self.distance_matrix[0][1],
                seed_used=self.config.seed or random.randint(0, 2**32 - 1),
                generations_completed=0,
                convergence_history=[self.distance_matrix[0][1]],
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )
        
        # Initialize population
        population = self._initialize_population()
        
        # Evaluate initial population
        evaluated_pop = [(ind, self._calculate_fitness(ind)) for ind in population]
        
        # Track best
        best_ind, best_fit = min(evaluated_pop, key=lambda x: x[1])
        self.best_individual = best_ind[:]
        self.best_fitness = best_fit
        self.convergence_history.append(best_fit)
        
        # Evolution loop
        for generation in range(self.config.generations):
            # Selection
            selected = self._tournament_selection(evaluated_pop)
            
            # Crossover
            offspring = self._crossover(selected)
            
            # Mutation
            mutated = self._mutate(offspring)
            
            # Evaluate offspring
            evaluated_offspring = [(ind, self._calculate_fitness(ind)) for ind in mutated]
            
            # Elitism: keep best individuals from previous generation
            evaluated_pop.sort(key=lambda x: x[1])
            elites = [ind for ind, _ in evaluated_pop[:self.config.elitism_count]]
            
            # Replace population with offspring + elites
            population = elites + [ind for ind, _ in evaluated_offspring[:self.config.population_size - self.config.elitism_count]]
            evaluated_pop = [(ind, self._calculate_fitness(ind)) for ind in population]
            
            # Update best
            current_best_ind, current_best_fit = min(evaluated_pop, key=lambda x: x[1])
            if current_best_fit < self.best_fitness:
                self.best_individual = current_best_ind[:]
                self.best_fitness = current_best_fit
            
            self.convergence_history.append(self.best_fitness)
        
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        seed_used = self.config.seed if self.config.seed is not None else random.randint(0, 2**32 - 1)
        
        return GAResult(
            best_order=self.best_individual,
            best_distance=self.best_fitness,
            seed_used=seed_used,
            generations_completed=self.config.generations,
            convergence_history=self.convergence_history[:],
            execution_time_ms=execution_time_ms
        )
    
    def _initialize_population(self) -> List[List[int]]:
        """Initialize random population with start point fixed at index 0."""
        population = []
        variable_indices = list(range(1, self.num_stops))
        
        for _ in range(self.config.population_size):
            individual = [0] + random.sample(variable_indices, len(variable_indices))
            population.append(individual)
        
        return population
    
    def _calculate_fitness(self, individual: List[int]) -> float:
        """
        Calculate total distance for a route ordering.
        Lower distance = better fitness.
        """
        total_distance = 0.0
        for i in range(len(individual) - 1):
            from_idx = individual[i]
            to_idx = individual[i + 1]
            total_distance += self.distance_matrix[from_idx][to_idx]
        return total_distance
    
    def _tournament_selection(self, evaluated_pop: List[Tuple[List[int], float]]) -> List[List[int]]:
        """
        Tournament selection: pick k random individuals, select the best one.
        Repeat to create mating pool.
        """
        selected = []
        for _ in range(self.config.population_size):
            # Random tournament participants
            tournament = random.sample(evaluated_pop, self.config.tournament_size)
            # Select best fitness (lowest distance)
            winner = min(tournament, key=lambda x: x[1])
            selected.append(winner[0][:])  # Copy the individual
        return selected
    
    def _crossover(self, population: List[List[int]]) -> List[List[int]]:
        """
        Ordered Crossover (OX) for permutation preservation.
        Maintains relative order while combining parent sequences.
        """
        offspring = []
        
        for i in range(0, len(population) - 1, 2):
            parent1 = population[i]
            parent2 = population[i + 1]
            
            if random.random() < self.config.crossover_rate:
                child1, child2 = self._ordered_crossover(parent1, parent2)
                offspring.extend([child1, child2])
            else:
                offspring.extend([parent1[:], parent2[:]])
        
        # Handle odd population size
        if len(population) % 2 == 1:
            offspring.append(population[-1][:])
        
        return offspring
    
    def _ordered_crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """
        Ordered Crossover implementation.
        Selects a segment from parent1 and fills remaining positions with order from parent2.
        """
        n = len(parent1)
        
        # Select random crossover points (excluding index 0 which is fixed start)
        start = random.randint(1, n - 2)
        end = random.randint(start + 1, n - 1)
        
        def create_child(p1, p2):
            child = [None] * n
            child[0] = 0  # Keep start fixed
            
            # Copy segment from p1
            for i in range(start, end + 1):
                child[i] = p1[i]
            
            # Fill remaining with order from p2
            p2_remaining = [gene for gene in p2 if gene not in child]
            
            idx = 1
            for i in range(1, n):
                if child[i] is None:
                    child[i] = p2_remaining[idx - 1]
                    idx += 1
            
            return child
        
        child1 = create_child(parent1, parent2)
        child2 = create_child(parent2, parent1)
        
        return child1, child2
    
    def _mutate(self, population: List[List[int]]) -> List[List[int]]:
        """
        Apply mutation operators: swap and inversion.
        Only mutates the variable portion (indices 1 onwards).
        """
        mutated = []
        
        for individual in population:
            if random.random() < self.config.mutation_rate:
                # Choose between swap and inversion mutation
                if random.random() < 0.5:
                    mutated.append(self._swap_mutation(individual))
                else:
                    mutated.append(self._inversion_mutation(individual))
            else:
                mutated.append(individual[:])
        
        return mutated
    
    def _swap_mutation(self, individual: List[int]) -> List[int]:
        """Swap two random positions (excluding index 0)."""
        mutant = individual[:]
        n = len(mutant)
        
        if n <= 2:
            return mutant
        
        i = random.randint(1, n - 1)
        j = random.randint(1, n - 1)
        
        mutant[i], mutant[j] = mutant[j], mutant[i]
        return mutant
    
    def _inversion_mutation(self, individual: List[int]) -> List[int]:
        """Invert a random segment (excluding index 0)."""
        mutant = individual[:]
        n = len(mutant)
        
        if n <= 2:
            return mutant
        
        start = random.randint(1, n - 2)
        end = random.randint(start + 1, n - 1)
        
        # Reverse the segment
        mutant[start:end + 1] = mutant[start:end + 1][::-1]
        return mutant


def nearest_neighbour_ordering(distance_matrix: List[List[float]]) -> List[int]:
    """
    Deterministic nearest-neighbor baseline for multi-stop routing.
    Start point (index 0) is fixed; selects nearest unvisited stop at each step.
    Uses deterministic tie-breaking by smallest index.
    
    Args:
        distance_matrix: N x N distance matrix
    
    Returns:
        Ordered list of indices starting with 0
    """
    n = len(distance_matrix)
    if n == 0:
        return []
    if n == 1:
        return [0]
    if n == 2:
        return [0, 1]
    
    unvisited = set(range(1, n))
    order = [0]
    current = 0
    
    while unvisited:
        # Find nearest unvisited neighbor
        nearest = min(
            unvisited,
            key=lambda idx: (distance_matrix[current][idx], idx)  # Tie-break by index
        )
        order.append(nearest)
        unvisited.remove(nearest)
        current = nearest
    
    return order
