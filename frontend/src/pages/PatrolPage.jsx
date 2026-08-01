import { useMemo } from "react";
import CrimeMap from "../components/map/CrimeMap";
import { useAppContext } from "../store/AppContext";
import { buildDashboardDataset } from "../lib/dataset";

const baseDataset = buildDashboardDataset([], [], null);
const dijkstraRoute = {
  id: "dijkstra",
  label: "Dijkstra",
  distanceKm: 14.2,
  fuelLitres: 3.4,
  timeMinutes: 48,
  computeMs: 124,
  waypoints: baseDataset.route.dijkstra.waypoints,
};

const geneticRoute = {
  id: "genetic",
  label: "Genetic Algorithm",
  distanceKm: 12.8,
  fuelLitres: 2.7,
  timeMinutes: 54,
  computeMs: 318,
  waypoints: baseDataset.route.genetic.waypoints,
};

export default function PatrolPage() {
  const { setRoute, hotspots, incidents } = useAppContext();

  const summary = useMemo(() => {
    const fuelReduction = ((dijkstraRoute.fuelLitres - geneticRoute.fuelLitres) / dijkstraRoute.fuelLitres) * 100;
    const timeDelta = ((geneticRoute.timeMinutes - dijkstraRoute.timeMinutes) / dijkstraRoute.timeMinutes) * 100;

    return {
      fuelReduction: fuelReduction.toFixed(1),
      timeDelta: timeDelta.toFixed(1),
    };
  }, []);

  const handleRunComparison = () => {
    setRoute({ dijkstra: dijkstraRoute, genetic: geneticRoute });
  };

  return (
    <div className="page-stack">
      <section className="panel patrol-toolbar">
        <div>
          <p className="eyebrow">Patrol optimization</p>
          <h2>Route comparison and decision support</h2>
        </div>
        <button type="button" onClick={handleRunComparison}>Run comparison</button>
      </section>

      <section className="patrol-grid">
        <article className="panel">
          <h3>Dijkstra</h3>
          <p>Distance: {dijkstraRoute.distanceKm} km</p>
          <p>Fuel: {dijkstraRoute.fuelLitres} litres</p>
          <p>Time: {dijkstraRoute.timeMinutes} min</p>
          <p>Compute: {dijkstraRoute.computeMs} ms</p>
        </article>
        <article className="panel">
          <h3>Genetic algorithm</h3>
          <p>Distance: {geneticRoute.distanceKm} km</p>
          <p>Fuel: {geneticRoute.fuelLitres} litres</p>
          <p>Time: {geneticRoute.timeMinutes} min</p>
          <p>Compute: {geneticRoute.computeMs} ms</p>
        </article>
      </section>

      <section className="panel result-card">
        <h3>Result</h3>
        <p>GA achieves {summary.fuelReduction}% fuel reduction at {summary.timeDelta}% more time.</p>
      </section>

      <div className="map-shell">
        <CrimeMap hotspots={hotspots} incidents={incidents} patrolRoute={{ dijkstra: dijkstraRoute, genetic: geneticRoute }} />
      </div>
    </div>
  );
}
