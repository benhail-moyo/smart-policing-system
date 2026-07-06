import DashboardOverview from "../components/dashboard/DashboardOverview";
import StatsPanel from "../components/dashboard/StatsPanel";
import CrimeMap from "../components/map/CrimeMap";
import IncidentForm from "../components/reports/IncidentForm";
import { useAppContext } from "../store/AppContext";

export default function DashboardPage() {
  const { hotspots, incidents, activeRoute } = useAppContext();

  return (
    <div className="page-stack">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Operations overview</p>
          <h2>Harare policing command centre</h2>
          <p className="page-copy">Monitor incidents, hotspot pressure, and patrol performance from one view.</p>
        </div>
        <StatsPanel />
      </section>

      <section className="dashboard-grid">
        <DashboardOverview />
        <CrimeMap hotspots={hotspots} incidents={incidents} patrolRoute={activeRoute} />
        <IncidentForm />
      </section>
    </div>
  );
}
