# Phase 5: Frontend Dashboard

> **Prerequisite:** Phases 1–4 complete. All API endpoints working.  
> **Estimated time:** 8–12 hours  
> **This phase is done when:** A browser shows the crime map with hotspots, the incident submission form works, and the patrol route comparison view renders both routes.

---

## Context for Claude

Building the React frontend for Crime-Watch. This is a law enforcement decision-support dashboard, not a consumer app. Design priorities:
1. **Clarity over aesthetics** — officers need fast, unambiguous information
2. **Map-first layout** — the map is the primary interface
3. **Minimal clicks** — critical functions reachable in ≤2 clicks
4. **Works on low-bandwidth** — Zimbabwe connectivity constraint (dissertation Section 1.6)

Tech: React 18, Leaflet.js (via react-leaflet), axios for API calls, React Context for state.

---

## Project Setup

```bash
cd frontend/
npx create-react-app . --template cra-template
# OR if React 18 + Vite is available:
npm create vite@latest . -- --template react
# Install dependencies
npm install react-leaflet leaflet axios react-router-dom recharts
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**`package.json` — add proxy for API calls during development:**
```json
{
  "proxy": "http://localhost:5000"
}
```

---

## Application Structure

### 5.1 React Context Store

Create `src/store/AppContext.jsx`:

```jsx
import { createContext, useContext, useReducer } from 'react';

const initialState = {
  user: null,          // { id, email, role }
  token: null,         // JWT token
  incidents: [],
  hotspots: [],
  activeRoute: null,   // Current patrol route displayed on map
  stats: null,         // Dashboard summary stats
};

// Actions: SET_USER, SET_INCIDENTS, SET_HOTSPOTS, SET_ROUTE, SET_STATS, LOGOUT

const AppContext = createContext(null);
export const useAppContext = () => useContext(AppContext);
export const AppProvider = ({ children }) => { /* reducer implementation */ };
```

Store the JWT token in `localStorage` (acceptable for a proof-of-concept; note session storage as a more secure alternative in dissertation).

### 5.2 API Service Layer

Create `src/services/api.js`:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Inject JWT token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('crimewatch_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 — token expired
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('crimewatch_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (email, password, role) => api.post('/auth/register', { email, password, role }),
};

export const incidentsAPI = {
  submit: (data) => api.post('/incidents/', data),
  list: (params) => api.get('/incidents/', { params }),
  stats: () => api.get('/incidents/stats'),
};

export const hotspotsAPI = {
  list: () => api.get('/hotspots/'),
  analyze: (days_back = 30) => api.post('/hotspots/analyze', { days_back }),
  heatmap: (bbox) => api.get('/hotspots/heatmap', { params: bbox }),
};

export const patrolAPI = {
  compare: (hotspot_ids) => api.post('/patrol/compare', { hotspot_ids }),
  optimize: (data) => api.post('/patrol/optimize', data),
  routes: () => api.get('/patrol/routes'),
};
```

### 5.3 Pages and Routing

Create `src/App.jsx` with these routes:
```
/login          → LoginPage
/               → DashboardPage (protected)
/map            → MapPage (protected)
/incidents      → IncidentsPage (protected)
/patrol         → PatrolPage (officers only)
```

Use `<PrivateRoute>` component that checks `token` from context.

### 5.4 The Crime Map Component

This is the most important component. Create `src/components/map/CrimeMap.jsx`:

```jsx
import { MapContainer, TileLayer, Circle, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Harare center coordinates
const HARARE_CENTER = [-17.8292, 31.0522];
const DEFAULT_ZOOM = 12;

export default function CrimeMap({ hotspots, incidents, patrolRoute }) {
  // Color by risk score
  const getRiskColor = (score) => {
    if (score >= 0.7) return '#dc2626'; // red — HIGH
    if (score >= 0.4) return '#ea580c'; // orange — MEDIUM
    return '#ca8a04';                    // yellow — LOW
  };

  return (
    <MapContainer center={HARARE_CENTER} zoom={DEFAULT_ZOOM} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />
      
      {/* Hotspot circles — radius proportional to risk score */}
      {hotspots.map((h) => (
        <Circle
          key={h.id}
          center={[h.centroid.lat, h.centroid.lng]}
          radius={500 + (h.risk_score * 1000)}
          pathOptions={{
            color: getRiskColor(h.risk_score),
            fillColor: getRiskColor(h.risk_score),
            fillOpacity: 0.3,
            weight: 2,
          }}
        >
          <Popup>
            <strong>Hotspot #{h.id}</strong><br />
            Category: {h.dominant_category}<br />
            Incidents: {h.incident_count}<br />
            Risk Score: {(h.risk_score * 100).toFixed(0)}%
          </Popup>
        </Circle>
      ))}
      
      {/* Patrol route overlay */}
      {patrolRoute && (
        <Polyline
          positions={patrolRoute.waypoints}
          pathOptions={{ color: '#2563eb', weight: 3, dashArray: '10, 5' }}
        />
      )}
    </MapContainer>
  );
}
```

**Note:** Use OpenStreetMap tiles — free, no API key required.

### 5.5 Dashboard Statistics Panel

Create `src/components/dashboard/StatsPanel.jsx`:

Displays 4 key metrics as cards:
- Total incidents this week
- HIGH severity incidents (red badge)
- Active hotspots count
- Last patrol route fuel estimate

Use `recharts` for a simple bar chart of incidents by severity.

### 5.6 Incident Submission Form

Create `src/components/reports/IncidentForm.jsx`:

```jsx
// Fields:
// - Text area: "Describe the incident" (placeholder in English, Shona, Ndebele)
// - Map click to set location (or manual lat/lng entry)
// - Location description (text input)
// On submit: calls incidentsAPI.submit()
// On success: shows triage result in a modal:
//   "Classified as: ROBBERY | Severity: HIGH | Confidence: 87%"
```

### 5.7 Patrol Route Comparison View

Create `src/pages/PatrolPage.jsx` — this is the academic showcase screen.

Layout:
```
┌─────────────────────────────────────────────────────────┐
│  PATROL OPTIMIZATION                   [Run Comparison]  │
├──────────────────────────┬──────────────────────────────┤
│  DIJKSTRA                │  GENETIC ALGORITHM           │
│  Distance: X km          │  Distance: Y km              │
│  Fuel: A litres          │  Fuel: B litres              │
│  Time: P min             │  Time: Q min                 │
│  Compute: M ms           │  Compute: N ms               │
├──────────────────────────┴──────────────────────────────┤
│  RESULT: GA achieves X% fuel reduction at Y% more time  │
├─────────────────────────────────────────────────────────┤
│  [MAP showing both routes in different colors]          │
└─────────────────────────────────────────────────────────┘
```

Dijkstra route in blue, GA route in green. Both overlaid on the same map instance.

---

## Acceptance Checklist

Manual testing in browser:

```
□ Login page loads at /login
□ Invalid credentials shows error message (not a crash)
□ After login, redirected to dashboard
□ Dashboard shows incident stats (calls /incidents/stats)
□ Map page renders OpenStreetMap tiles centered on Harare
□ Hotspots appear as colored circles (run analysis first via API)
□ Clicking a hotspot shows popup with details
□ Incident form submits and shows triage result
□ Patrol page shows comparison table after clicking "Run Comparison"
□ Both routes visible on map in different colors
□ Community user does NOT see Patrol menu item
□ Logout clears token and redirects to /login
```

---

## Dissertation Notes for This Phase

**Chapter 3 (Methodology) — Frontend Architecture:**
- Describe the component hierarchy: App → Pages → Components → Services
- Mention React Context as the state management approach (justify why not Redux: system is small, overkill)
- Note that Leaflet.js was chosen for GIS capability without Google Maps API costs

**Chapter 4 — Screenshots required:**
- Figure 4.A: Dashboard overview showing stats panel
- Figure 4.B: Crime map with hotspot overlays (the most visually impressive screenshot)
- Figure 4.C: Incident submission with triage result modal
- Figure 4.D: Patrol comparison view with both routes on map

**Accessibility note for dissertation:**
The color scheme (red/orange/yellow for risk) may be problematic for colorblind users. Document this as a known limitation and propose accessible alternatives (patterns, shapes) as future work.

---

## What You Learn in This Phase

- **React component architecture:** Pages contain logic, components are reusable views. This separation is how every serious React codebase is organized.
- **API integration pattern:** The axios interceptor for JWT injection means you add auth to every request in one place, not in every component. DRY principle.
- **Map rendering:** Leaflet is used in production by government agencies, logistics companies, and NGOs worldwide. It works offline (with cached tiles), which matters for Zimbabwe deployment.
- **Role-based UI:** Hiding the Patrol menu from community users is the frontend complement to backend role enforcement. Both layers must check roles independently.
