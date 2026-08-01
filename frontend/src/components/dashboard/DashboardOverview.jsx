import { useAppContext } from "../../store/AppContext";

export default function DashboardOverview() {
  const { incidents, hotspots, activeRoute, stats } = useAppContext();

  const escalated = incidents.filter((incident) => incident.severity === "HIGH" || incident.severity === "CRITICAL").length;
  const routeLabel = activeRoute?.label || "No route loaded";

  return (
    <aside className="panel overview-panel">
      <div className="panel-heading">
        <p className="eyebrow">Operations health</p>
        <h2>Command overview</h2>
      </div>
      <div className="metric-stack">
        <div className="metric-card">
          <span>Live incidents</span>
          <strong>{stats?.totalIncidents ?? incidents.length}</strong>
        </div>
        <div className="metric-card">
          <span>Escalated cases</span>
          <strong>{escalated}</strong>
        </div>
        <div className="metric-card">
          <span>Active hotspots</span>
          <strong>{stats?.activeHotspots ?? hotspots.length}</strong>
        </div>
        <div className="metric-card">
          <span>Patrol plan</span>
          <strong>{routeLabel}</strong>
        </div>
      </div>
    </aside>
  );
}
