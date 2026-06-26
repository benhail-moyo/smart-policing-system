from math import atan2, cos, radians, sin, sqrt


class DijkstraSolver:
    def __init__(self, waypoints):
        self.waypoints = list(waypoints)

    def solve(self):
        if len(self.waypoints) <= 2:
            return self.waypoints

        start = self.waypoints[0]
        unvisited = self.waypoints[1:]
        route = [start]
        current = start

        while unvisited:
            nearest = min(unvisited, key=lambda point: _distance_km(current, point))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest

        return route


def _distance_km(a, b):
    lat1, lng1 = a
    lat2, lng2 = b
    radius_km = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    value = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return radius_km * 2 * atan2(sqrt(value), sqrt(1 - value))
