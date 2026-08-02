/**
 * LoginPage — mirrors prototype login/page.tsx
 * Supports Sign in / Register tabs + quick demo access buttons.
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, UserPlus, LogIn, Car, Users, Loader2 } from "lucide-react";
import { api, setAuth, getStoredUser } from "../lib/client";

const API = import.meta.env.VITE_API_BASE_URL || "/api/v1";

// Demo users — used as fallback when backend is offline
const DEMO_USERS = {
  "officer@harare.gov.zw": {
    name: "Officer Demo",
    email: "officer@harare.gov.zw",
    role: "officer",
  },
  "community@harare.gov.zw": {
    name: "Community Member",
    email: "community@harare.gov.zw",
    role: "community",
  },
};

const MOCK_TOKEN = "demo.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo";

export default function LoginPage() {
  const navigate = useNavigate();
  const [mode, setMode]       = useState("login"); // "login" | "register"
  const [name, setName]       = useState("");
  const [email, setEmail]     = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole]       = useState("community");
  const [error, setError]     = useState(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    if (getStoredUser()) navigate("/", { replace: true });
  }, [navigate]);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const path    = mode === "login" ? `${API}/auth/login` : `${API}/auth/register`;
      const payload = mode === "login"
        ? { email, password }
        : { name, email, password, role };

      const res = await api(path, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      const token    = res.access_token ?? res.token;
      const userRole = email.includes("officer") ? "officer" : "community";
      const user     = res.user ?? { email, name: name || email.split("@")[0], role: userRole };
      if (!token) throw new Error("Authentication failed — no token returned");
      setAuth(token, user);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function demoLogin(demoEmail) {
    setError(null);
    setSeeding(true);
    const demoUser = DEMO_USERS[demoEmail];

    try {
      // Try the real backend first
      const res   = await api(`${API}/auth/login`, {
        method: "POST",
        body: JSON.stringify({ email: demoEmail, password: "password123" }),
      });
      const token = res.access_token ?? res.token;
      // Backend stub returns no user object — always build it from DEMO_USERS map
      const user  = res.user ?? demoUser ?? { email: demoEmail, name: demoEmail.split("@")[0], role: "community" };
      if (!token) throw new Error("Demo login failed — no token");
      setAuth(token, user);
      navigate("/", { replace: true });
    } catch (err) {
      // If the backend is down or returns an error, fall back to a local mock session.
      // This lets the demo buttons always work for UI exploration.
      if (demoUser) {
        setAuth(MOCK_TOKEN, demoUser);
        navigate("/", { replace: true });
      } else {
        setError(err.message);
      }
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="cw-login-page">
      <div className="cw-login-box">
        {/* Logo */}
        <div className="cw-login-logo-wrap">
          <div className="cw-login-icon">
            <Shield size={48} color="#60a5fa" />
          </div>
          <h1 className="cw-login-title">Harare Crime Watch</h1>
          <p className="cw-login-sub">Community safety intelligence platform</p>
        </div>

        <div className="cw-login-card">
          {/* Mode tabs */}
          <div className="cw-mode-tabs">
            {["login", "register"].map((m) => {
              const Icon = m === "login" ? LogIn : UserPlus;
              return (
                <button
                  key={m}
                  onClick={() => { setMode(m); setError(null); }}
                  className={`cw-mode-tab ${mode === m ? "active" : "inactive"}`}
                >
                  <Icon size={14} />
                  {m === "login" ? "Sign in" : "Register"}
                </button>
              );
            })}
          </div>

          {/* Form */}
          <form onSubmit={submit} className="cw-auth-form">
            {mode === "register" && (
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Full name"
                required
                className="cw-form-input"
              />
            )}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              required
              className="cw-form-input"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
              className="cw-form-input"
            />
            {mode === "register" && (
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="cw-form-select"
              >
                <option value="community">Community member</option>
                <option value="officer">Patrol officer</option>
              </select>
            )}

            {error && <div className="cw-error-box">{error}</div>}

            <button type="submit" disabled={loading} className="cw-submit-btn">
              {loading
                ? <Loader2 size={16} className="cw-spin" />
                : mode === "login" ? <LogIn size={16} /> : <UserPlus size={16} />
              }
              {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          {/* Demo buttons */}
          <div className="cw-demo-divider">
            <p className="cw-demo-label">Quick demo access</p>
            <div className="cw-demo-grid">
              <button
                disabled={seeding}
                onClick={() => demoLogin("officer@harare.gov.zw")}
                className="cw-demo-btn"
              >
                {seeding ? <Loader2 size={16} className="cw-spin" /> : <Car size={16} />}
                Patrol Officer
              </button>
              <button
                disabled={seeding}
                onClick={() => demoLogin("community@harare.gov.zw")}
                className="cw-demo-btn"
              >
                {seeding ? <Loader2 size={16} className="cw-spin" /> : <Users size={16} />}
                Community Member
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
