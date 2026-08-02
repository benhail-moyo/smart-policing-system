// Crime types and triage logic — ported from prototype's crime.ts
export const HARARE_CENTER = { lat: -17.8292, lng: 31.0522 };

export const CRIME_TYPES = [
  "Armed Robbery",
  "Assault",
  "Burglary",
  "Carjacking",
  "Theft",
  "Vandalism",
  "Drug Offense",
  "Fraud",
  "Public Disturbance",
  "Kidnapping",
];

// ── Severity colour maps (prototype exact values) ──────────────────────────

export const PRIORITY_COLOR = {
  critical: "#dc2626",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#22c55e",
};

// Map backend severity strings (HIGH/MEDIUM/LOW) to priority colours
export const SEVERITY_COLOR = {
  HIGH:     "#dc2626",
  MEDIUM:   "#eab308",
  LOW:      "#22c55e",
  CRITICAL: "#dc2626",
};

// Hotspot level colours (matching prototype LEVEL_COLOR)
export const LEVEL_COLOR = {
  high:   "#dc2626",
  medium: "#f97316",
  low:    "#eab308",
};

// Patrol route colours
export const PATROL_ROUTES = [
  {
    id: "route-a",
    name: "Route A — CBD & Avenues",
    color: "#2563eb",
    waypoints: [
      { lat: -17.8292, lng: 31.0522 },
      { lat: -17.8252, lng: 31.0475 },
      { lat: -17.8189, lng: 31.0433 },
      { lat: -17.8151, lng: 31.0512 },
      { lat: -17.8215, lng: 31.0585 },
      { lat: -17.8292, lng: 31.0522 },
    ],
  },
  {
    id: "route-b",
    name: "Route B — Mbare & Southern Ring",
    color: "#f97316",
    waypoints: [
      { lat: -17.8292, lng: 31.0522 },
      { lat: -17.8451, lng: 31.0389 },
      { lat: -17.8564, lng: 31.0301 },
      { lat: -17.8611, lng: 31.0455 },
      { lat: -17.8489, lng: 31.0603 },
      { lat: -17.8292, lng: 31.0522 },
    ],
  },
];
