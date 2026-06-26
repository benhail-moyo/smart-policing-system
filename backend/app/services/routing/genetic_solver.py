import random

from app.services.routing.dijkstra_solver import _distance_km


class GeneticSolver:
    def __init__(
        self,
        waypoints,
        hotspot_weights=None,
        pop_size=100,
        generations=200,
        mutation_rate=0.02,
        crossover_rate=0.8,
    ):
        self.waypoints = list(waypoints)
        self.hotspot_weights = hotspot_weights or [1.0 for _ in self.waypoints]
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.fitness_history = []

    def solve(self):
        if len(self.waypoints) <= 2:
            return self.waypoints

        start = self.waypoints[0]
        middle = self.waypoints[1:]
        best = middle[:]
        best_score = self._score([start] + best)

        for _ in range(self.generations):
            candidate = best[:]
            if len(candidate) >= 2 and random.random() < self.crossover_rate:
                i, j = random.sample(range(len(candidate)), 2)
                candidate[i], candidate[j] = candidate[j], candidate[i]
            if len(candidate) >= 2 and random.random() < self.mutation_rate:
                random.shuffle(candidate)

            candidate_route = [start] + candidate
            score = self._score(candidate_route)
            if score < best_score:
                best = candidate
                best_score = score
            self.fitness_history.append(round(best_score, 5))

        return [start] + best

    def _score(self, route):
        return sum(_distance_km(route[i], route[i + 1]) for i in range(len(route) - 1))
