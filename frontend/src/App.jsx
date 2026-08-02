import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Map,
  Siren,
  Car,
  BrainCircuit,
  Shield,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { getStoredUser, clearAuth, isPatrolAllowed } from "./lib/client";
import LoginPage  from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import MapPage    from "./pages/MapPage";
import ReportPage from "./pages/ReportPage";
import PatrolPage from "./pages/PatrolPage";
import AnalysisPage from "./pages/AnalysisPage";

const NAV = [
  { to: "/",        label: "Dashboard",       Icon: LayoutDashboard, patrolOnly: false },
  { to: "/map",     label: "Crime Map",        Icon: Map,             patrolOnly: false },
  { to: "/report",  label: "Report Incident",  Icon: Siren,           patrolOnly: false },
  { to: "/patrol",  label: "Patrol Routes",    Icon: Car,             patrolOnly: true  },
  { to: "/analysis",label: "AI Analysis",      Icon: BrainCircuit,    patrolOnly: false },
];

function ProtectedRoute({ children }) {
  const user = getStoredUser();
  return user ? children : <Navigate to="/login" replace />;
}

function AppShell({ children }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(getStoredUser());

  // Keep user state in sync with localStorage
  useEffect(() => {
    const u = getStoredUser();
    if (!u) { navigate("/login", { replace: true }); return; }
    setUser(u);
  }, [navigate]);

  function logout() {
    clearAuth();
    setUser(null);
    navigate("/login", { replace: true });
  }

  if (!user) {
    return (
      <div style={{ display:"flex", minHeight:"100vh", alignItems:"center", justifyContent:"center", background:"#020617", color:"#94a3b8" }}>
        Loading…
      </div>
    );
  }

  const items = NAV.filter((n) => !n.patrolOnly || isPatrolAllowed(user));

  return (
    <div className="cw-shell">
      {/* ── Desktop sidebar ─────────────────────────────────────────────── */}
      <aside className="cw-sidebar">
        <div className="cw-brand">
          <Shield className="cw-brand-icon" />
          <div>
            <div className="cw-brand-title">HARARE</div>
            <div className="cw-brand-sub">Crime Watch</div>
          </div>
        </div>

        <nav className="cw-nav">
          {items.map((n) => {
            const Icon = n.Icon;
            return (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                className={({ isActive }) =>
                  `cw-nav-link${isActive ? " active" : ""}`
                }
              >
                <Icon className="cw-nav-icon" />
                {n.label}
                {/* ChevronRight shown for active item — added via CSS :has or inline */}
                <span className="cw-nav-chevron"><ChevronRight size={12} /></span>
              </NavLink>
            );
          })}
        </nav>

        <div className="cw-sidebar-footer">
          <div className="cw-user-info">
            <div className="cw-user-name">{user.name ?? user.email}</div>
            <div className="cw-user-role">{user.role}</div>
          </div>
          <button onClick={logout} className="cw-logout-btn">
            <LogOut size={14} />
            Log out
          </button>
        </div>
      </aside>

      {/* ── Mobile header + bottom nav ───────────────────────────────────── */}
      <div className="cw-main">
        <header className="cw-mobile-header">
          <div className="cw-mobile-brand">
            <Shield size={18} color="#60a5fa" />
            <span>Crime Watch</span>
          </div>
          <button onClick={logout} className="cw-mobile-logout">
            <LogOut size={14} />
            Log out
          </button>
        </header>

        <nav className="cw-mobile-nav">
          {items.map((n) => {
            const Icon = n.Icon;
            return (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                className={({ isActive }) =>
                  `cw-mobile-nav-link${isActive ? " active" : ""}`
                }
              >
                <Icon size={14} />
                {n.label}
              </NavLink>
            );
          })}
        </nav>

        <main className="cw-content">{children}</main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppShell>
              <Routes>
                <Route path="/"         element={<DashboardPage />} />
                <Route path="/map"      element={<MapPage />} />
                <Route path="/report"   element={<ReportPage />} />
                <Route path="/patrol"   element={<PatrolPage />} />
                <Route path="/analysis" element={<AnalysisPage />} />
                <Route path="*"         element={<Navigate to="/" replace />} />
              </Routes>
            </AppShell>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
