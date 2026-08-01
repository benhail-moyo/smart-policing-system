import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AlertTriangle, LayoutDashboard, LogOut, MapPinned, Route as RouteIcon, ShieldCheck, FileText } from "lucide-react";
import DashboardPage from "./pages/DashboardPage.jsx";
import IncidentsPage from "./pages/IncidentsPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import MapPage from "./pages/MapPage.jsx";
import PatrolPage from "./pages/PatrolPage.jsx";
import { useAppContext } from "./store/AppContext.jsx";

const baseNavItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/incidents", label: "Incidents", icon: FileText },
  { to: "/map", label: "Map", icon: MapPinned },
  { to: "/patrol", label: "Patrol", icon: RouteIcon, officerOnly: true },
];

function ProtectedRoute({ children }) {
  const { token } = useAppContext();
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const { user, logout } = useAppContext();
  const location = useLocation();
  const navItems = baseNavItems.filter((item) => !item.officerOnly || user?.role === "officer" || user?.role === "admin");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <ShieldCheck size={24} />
          <div>
            <p className="eyebrow">Crime-Watch</p>
            <h1>Operations centre</h1>
          </div>
        </div>

        <nav className="nav-links">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <AlertTriangle size={18} />
            <div>
              <strong>{user?.email || "Officer"}</strong>
              <span>{user?.role || "Field officer"}</span>
            </div>
          </div>
          <button type="button" className="secondary-button" onClick={logout}>
            <LogOut size={16} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <div className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">Smart policing</p>
            <h2>{location.pathname === "/" ? "Dashboard" : location.pathname.replace("/", "").replace(/^./, (char) => char.toUpperCase())}</h2>
          </div>
          <div className="topbar-pill">Real-time dispatch view</div>
        </header>

        <main className="content-area">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/incidents" element={<ProtectedRoute><IncidentsPage /></ProtectedRoute>} />
            <Route path="/map" element={<ProtectedRoute><MapPage /></ProtectedRoute>} />
            <Route path="/patrol" element={<ProtectedRoute><PatrolPage /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
