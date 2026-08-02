import DashboardOverview from "./components/dashboard/DashboardOverview.jsx";
import CrimeMap from "./components/map/CrimeMap.jsx";
import IncidentForm from "./components/reports/IncidentForm.jsx";

export default function App() {
  const { user, logout } = useAppContext();
  const location = useLocation();
  const navItems = baseNavItems.filter((item) => !item.officerOnly || user?.role === "officer" || user?.role === "admin");

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Crime-Watch</p>
          <h1>Smart Policing Operations Dashboard</h1>
        </div>
      </section>
      <section className="workspace">
        <DashboardOverview />
        <CrimeMap />
        <IncidentForm />
      </section>
    </main>
  );
}
