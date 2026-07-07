import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const data = [
  { name: "Low", incidents: 6 },
  { name: "Medium", incidents: 4 },
  { name: "High", incidents: 3 },
  { name: "Critical", incidents: 1 },
];

export default function StatsPanel() {
  return (
    <div className="stats-panel">
      <div className="stat-card">
        <span>Incidents this week</span>
        <strong>14</strong>
      </div>
      <div className="stat-card danger">
        <span>High severity</span>
        <strong>4</strong>
      </div>
      <div className="stat-card">
        <span>Active hotspots</span>
        <strong>3</strong>
      </div>
      <div className="stat-card">
        <span>Fuel estimate</span>
        <strong>18.4 L</strong>
      </div>
      <div className="chart-card">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="incidents" fill="#145c72" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
