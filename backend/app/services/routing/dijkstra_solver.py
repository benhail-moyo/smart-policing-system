from math import atan2, cos, radians, sin, sqrt


class DijkstraSolver:
    def __init__(self, waypoints):
        self.waypoints = list(waypoints)
        self.last_tour_indices = []

    def solve(self):
        if len(self.waypoints) == 0:
            self.last_tour_indices = []
            return []
        if len(self.waypoints) == 1:
            self.last_tour_indices = [0]
            return self.waypoints
        if len(self.waypoints) == 2:
            self.last_tour_indices = [0, 1]
            return self.waypoints

        # DISSERTATION CONTEXT:
        # This is not a full Dijkstra optimization of the TSP.
        # It is a greedy nearest-neighbor heuristic that uses shortest
        # inter-node distances to construct an O(n^2) patrol baseline.
        # The GA attempts to improve upon this deterministic baseline.
        unvisited = set(range(1, len(self.waypoints)))
        route_indices = [0]
        current_idx = 0

        while unvisited:
            nearest_idx = min(
                unvisited,
                key=lambda idx: _distance_km(self.waypoints[current_idx], self.waypoints[idx]),
            )
            route_indices.append(nearest_idx)
            unvisited.remove(nearest_idx)
            current_idx = nearest_idx

        self.last_tour_indices = route_indices
        return [self.waypoints[idx] for idx in route_indices]

    def get_tour_explanation(self, tour_indices=None):
        """Returns a human-readable waypoint sequence for debugging/results."""
        indices = tour_indices if tour_indices is not None else self.last_tour_indices
        return [
            {
                "step": step + 1,
                "lat": self.waypoints[idx][0],
                "lng": self.waypoints[idx][1],
            }
            for step, idx in enumerate(indices)
        ]


def _distance_km(a, b):
    lat1, lng1 = a
    lat2, lng2 = b
    radius_km = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    value = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return radius_km * 2 * atan2(sqrt(value), sqrt(1 - value))
