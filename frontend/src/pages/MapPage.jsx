import CrimeMap from "../components/map/CrimeMap";
import { useAppContext } from "../store/AppContext";

export default function MapPage() {
  const { hotspots, incidents, activeRoute } = useAppContext();

  return (
    <div className="page-stack">
      <section className="panel">
        <p className="eyebrow">Map view</p>
        <h2>Geographic incident and hotspot view</h2>
        <p className="page-copy">Hotspots are shown as risk-colored circles with route overlays on top.</p>
      </section>
      <div className="map-shell">
        <CrimeMap hotspots={hotspots} incidents={incidents} patrolRoute={activeRoute} />
      </div>
    </div>
  );
}
