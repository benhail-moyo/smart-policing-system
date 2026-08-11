from app.services.routing.dijkstra_solver import DijkstraSolver
from app.services.routing.route_engine import RouteEngine

WAYPOINTS = [
    (-17.8292, 31.0522),
    (-17.8677, 31.0359),
    (-17.8900, 31.0100),
]

print("Testing DijkstraSolver with 3 waypoints")
solver = DijkstraSolver(WAYPOINTS)
route = solver.solve()
print("Route:", route)

engine = RouteEngine()
dist = engine._calculate_total_distance(route)
print("Total distance (km):", dist)

# Test edge cases
print("Empty waypoints ->", DijkstraSolver([]).solve())
print("Single waypoint ->", DijkstraSolver([WAYPOINTS[0]]).solve())
print("Two waypoints ->", DijkstraSolver(WAYPOINTS[:2]).solve())
