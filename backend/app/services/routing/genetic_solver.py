import json
import copy
import random
import time
from pathlib import Path

from deap import base, creator, tools

from app.services.routing.dijkstra_solver import _distance_km


if not hasattr(creator, "FitnessMin"):
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMin)


class GeneticSolver:
    """
    Genetic Algorithm solver for patrol route ordering.

    The first waypoint is treated as the patrol base/current location and is
    kept fixed; the GA evolves permutations of the remaining hotspot waypoints.
    """

    def __init__(
        self,
        waypoints,
        hotspot_weights=None,
        pop_size=100,
        generations=200,
        mutation_rate=0.02,
        crossover_rate=0.8,
        alpha=0.15,
        seed=42,
    ):
        self.waypoints = list(waypoints)
        self.hotspot_weights = self._normalize_weights(hotspot_weights)
        self.pop_size = int(pop_size)
        self.generations = int(generations)
        self.mutation_rate = float(mutation_rate)
        self.crossover_rate = float(crossover_rate)
        self.alpha = float(alpha)
        self.seed = seed
        self.fitness_history = []
        self.best_individual = []

    def solve(self):
        if len(self.waypoints) == 0:
            self.best_individual = []
            return []
        if len(self.waypoints) <= 2:
            self.best_individual = list(range(len(self.waypoints)))
            return self.waypoints

        random.seed(self.seed)
        variable_indices = list(range(len(self.waypoints) - 1))
        toolbox = self._build_toolbox(variable_indices)

        population = toolbox.population(n=max(self.pop_size, 2))
        best = None

        for individual in population:
            individual.fitness.values = toolbox.evaluate(individual)

        for _ in range(max(self.generations, 1)):
            offspring = tools.selTournament(population, len(population), tournsize=3)
            offspring = list(map(toolbox.clone, offspring))

            for first, second in zip(offspring[::2], offspring[1::2]):
                if len(first) > 1 and random.random() < self.crossover_rate:
                    tools.cxOrdered(first, second)
                    del first.fitness.values
                    del second.fitness.values

            for mutant in offspring:
                if len(mutant) > 1 and random.random() < self.mutation_rate:
                    tools.mutShuffleIndexes(mutant, indpb=0.2)
                    del mutant.fitness.values

            invalid = [individual for individual in offspring if not individual.fitness.valid]
            for individual in invalid:
                individual.fitness.values = toolbox.evaluate(individual)

            population[:] = offspring
            current_best = tools.selBest(population, 1)[0]
            if best is None or current_best.fitness.values[0] < best.fitness.values[0]:
                best = toolbox.clone(current_best)
            self.fitness_history.append(round(best.fitness.values[0], 5))

        self.best_individual = [0] + [gene + 1 for gene in best]
        return [self.waypoints[idx] for idx in self.best_individual]

    def save_convergence_data(self, output_path: str = None):
        """
        Saves GA fitness curve to JSON for dissertation convergence plots.
        Call after solve().
        """
        if output_path is None:
            output_path = f"ml/routing/benchmarks/results/convergence_{int(time.time())}.json"

        data = {
            "generations": list(range(len(self.fitness_history))),
            "fitness": self.fitness_history,
            "parameters": {
                "pop_size": self.pop_size,
                "generations": self.generations,
                "mutation_rate": self.mutation_rate,
                "crossover_rate": self.crossover_rate,
                "alpha": self.alpha,
                "seed": self.seed,
            },
        }

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)

    def _build_toolbox(self, variable_indices):
        toolbox = base.Toolbox()
        toolbox.register("individual", self._make_individual, variable_indices)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("evaluate", self._evaluate)
        toolbox.register("clone", copy.deepcopy)
        return toolbox

    def _make_individual(self, variable_indices):
        values = list(variable_indices)
        random.shuffle(values)
        return creator.Individual(values)

    def _evaluate(self, individual):
        route_indices = [0] + [gene + 1 for gene in individual]
        distance = _total_distance([self.waypoints[idx] for idx in route_indices])

        weighted_latency = 0.0
        cumulative_distance = 0.0
        total_weight = sum(self.hotspot_weights) or 1.0
        for previous_idx, current_idx in zip(route_indices, route_indices[1:]):
            cumulative_distance += _distance_km(
                self.waypoints[previous_idx],
                self.waypoints[current_idx],
            )
            weighted_latency += cumulative_distance * self.hotspot_weights[current_idx]

        normalized_latency = weighted_latency / total_weight
        return (distance + (self.alpha * normalized_latency),)

    def _normalize_weights(self, weights):
        if not weights:
            return [1.0 for _ in self.waypoints]

        normalized = [float(weight or 0.0) for weight in weights]
        if len(normalized) < len(self.waypoints):
            normalized.extend([1.0] * (len(self.waypoints) - len(normalized)))
        return normalized[: len(self.waypoints)]


def _total_distance(route):
    return round(
        sum(_distance_km(route[i], route[i + 1]) for i in range(len(route) - 1)),
        3,
    )


def parameter_sensitivity_analysis(
    waypoints,
    weights,
    output_dir="ml/routing/benchmarks/results/",
):
    """
    Tests GA configurations for dissertation parameter sensitivity tables.
    """
    configs = [
        {"pop_size": 50, "generations": 100, "mutation_rate": 0.02},
        {"pop_size": 100, "generations": 200, "mutation_rate": 0.02},
        {"pop_size": 200, "generations": 200, "mutation_rate": 0.02},
        {"pop_size": 100, "generations": 200, "mutation_rate": 0.05},
        {"pop_size": 100, "generations": 300, "mutation_rate": 0.01},
    ]

    results = []
    for config in configs:
        solver = GeneticSolver(
            waypoints=waypoints,
            hotspot_weights=weights,
            crossover_rate=0.8,
            **config,
        )
        start = time.perf_counter()
        route = solver.solve()
        elapsed = (time.perf_counter() - start) * 1000

        results.append(
            {
                **config,
                "distance_km": _total_distance(route),
                "time_ms": round(elapsed, 1),
                "convergence_file": solver.save_convergence_data(
                    str(Path(output_dir) / f"sensitivity_{config['pop_size']}_{config['generations']}_{config['mutation_rate']}.json")
                ),
            }
        )

    return results
