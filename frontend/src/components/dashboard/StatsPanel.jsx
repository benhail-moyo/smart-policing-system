import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAppContext } from "../../store/AppContext";

export default function StatsPanel() {
  const { stats, activeRoute } = useAppContext();

  const chartData = [
    { name: "Low", incidents: stats?.bySeverity?.LOW || 0 },
    { name: "Medium", incidents: stats?.bySeverity?.MEDIUM || 0 },
    { name: "High", incidents: stats?.bySeverity?.HIGH || 0 },
    { name: "Critical", incidents: stats?.bySeverity?.CRITICAL || 0 },
  ];

  return (
    <div className="stats-panel">
      <div className="stat-card">
        <span>Incidents this week</span>
        <strong>{stats?.totalIncidents ?? 0}</strong>
      </div>
      <div className="stat-card danger">
        <span>High severity</span>
        <strong>{stats?.highSeverity ?? 0}</strong>
      </div>
      <div className="stat-card">
        <span>Hotspots under watch</span>
        <strong>{stats?.activeHotspots ?? 0}</strong>
      </div>
      <div className="stat-card">
        <span>Fuel estimate</span>
        <strong>{activeRoute?.fuelLitres ?? 0} L</strong>
      </div>
      <div className="chart-card">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#34495e" />
            <XAxis dataKey="name" tick={{ fill: "#9fb0c0" }} />
            <YAxis tick={{ fill: "#9fb0c0" }} />
            <Tooltip />
            <Bar dataKey="incidents" fill="#2ec4b6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
