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
] as const;

export type CrimeType = (typeof CRIME_TYPES)[number];

// Base danger weight per crime type (used in triage + hotspot weighting)
const TYPE_WEIGHT: Record<string, number> = {
  "Armed Robbery": 9,
  Carjacking: 8,
  Kidnapping: 10,
  Assault: 7,
  Burglary: 6,
  "Drug Offense": 5,
  Theft: 4,
  Fraud: 3,
  Vandalism: 3,
  "Public Disturbance": 2,
};

export type Priority = "critical" | "high" | "medium" | "low";

export type TriageResult = {
  priority: Priority;
  score: number;
  recommendation: string;
  eta: string;
};

export function triage(type: string, severity: number): TriageResult {
  const base = TYPE_WEIGHT[type] ?? 3;
  // severity 1..5 -> multiplier
  const score = Math.round(base * (0.6 + severity * 0.28) * 5);

  let priority: Priority;
  let recommendation: string;
  let eta: string;

  if (score >= 78) {
    priority = "critical";
    recommendation =
      "Dispatch armed response unit immediately. Alert nearest patrol and notify command center.";
    eta = "0-5 min";
  } else if (score >= 55) {
    priority = "high";
    recommendation =
      "Dispatch patrol unit as a priority. Keep reporter on the line for updates.";
    eta = "5-15 min";
  } else if (score >= 32) {
    priority = "medium";
    recommendation =
      "Queue for the next available patrol. Log details and monitor the area.";
    eta = "15-45 min";
  } else {
    priority = "low";
    recommendation =
      "Record for follow-up. Add to daily community patrol review.";
    eta = "1-4 hrs";
  }

  return { priority, score, recommendation, eta };
}

export const PRIORITY_ORDER: Priority[] = [
  "critical",
  "high",
  "medium",
  "low",
];

// ---- Hotspot analysis (grid clustering) ----

export type IncidentPoint = {
  lat: number;
  lng: number;
  severity: number;
  priority: string;
  type: string;
};

export type HotspotResult = {
  lat: number;
  lng: number;
  count: number;
  weight: number;
  radius: number;
  level: "high" | "medium" | "low";
  topTypes: string[];
};

const PRIORITY_WEIGHT: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

// Cluster incidents into a lat/lng grid (~700m cells) and score each cell.
export function analyzeHotspots(points: IncidentPoint[]): HotspotResult[] {
  const CELL = 0.0065; // ~700m
  const cells = new Map<
    string,
    {
      sumLat: number;
      sumLng: number;
      count: number;
      weight: number;
      types: Record<string, number>;
    }
  >();

  for (const p of points) {
    const gx = Math.floor(p.lat / CELL);
    const gy = Math.floor(p.lng / CELL);
    const key = `${gx}:${gy}`;
    const cell =
      cells.get(key) ??
      { sumLat: 0, sumLng: 0, count: 0, weight: 0, types: {} };
    cell.sumLat += p.lat;
    cell.sumLng += p.lng;
    cell.count += 1;
    const pw = PRIORITY_WEIGHT[p.priority] ?? 2;
    cell.weight += pw * (0.5 + p.severity * 0.1);
    cell.types[p.type] = (cell.types[p.type] ?? 0) + 1;
    cells.set(key, cell);
  }

  const results: HotspotResult[] = [];
  for (const cell of cells.values()) {
    if (cell.count < 2) continue; // need a cluster
    const topTypes = Object.entries(cell.types)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([t]) => t);

    let level: "high" | "medium" | "low" = "low";
    if (cell.weight >= 7) level = "high";
    else if (cell.weight >= 4) level = "medium";

    results.push({
      lat: cell.sumLat / cell.count,
      lng: cell.sumLng / cell.count,
      count: cell.count,
      weight: Math.round(cell.weight * 10) / 10,
      radius: Math.min(900, 300 + cell.count * 70),
      level,
      topTypes,
    });
  }

  return results.sort((a, b) => b.weight - a.weight);
}

// ---- Patrol routes ----

export type PatrolRoute = {
  id: string;
  name: string;
  color: string;
  waypoints: { lat: number; lng: number }[];
};

export const PATROL_ROUTES: PatrolRoute[] = [
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

// Haversine distance in km
export function haversineKm(
  a: { lat: number; lng: number },
  b: { lat: number; lng: number }
): number {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export function routeLengthKm(route: PatrolRoute): number {
  let total = 0;
  for (let i = 1; i < route.waypoints.length; i++) {
    total += haversineKm(route.waypoints[i - 1], route.waypoints[i]);
  }
  return Math.round(total * 100) / 100;
}
