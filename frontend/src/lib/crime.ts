// UI constants that remain in the frontend for display purposes

import api from "./api";

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

export type Priority = "critical" | "high" | "medium" | "low";

export type PatrolRoute = {
  id: string;
  name: string;
  color: string;
  waypoints: { lat: number; lng: number }[];
};

// Haversine distance in km (utility function for UI calculations)
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

// Call backend to compute route metrics (preferred). Falls back to client-side calculation when backend unavailable.
export async function fetchRouteMetrics(route: PatrolRoute): Promise<{ distanceKm: number; estMinutes: number; points: number }>{
  try {
    const res = await api.post<{ distanceKm: number; estMinutes: number; points: number }>(
      '/patrol/metrics',
      { waypoints: route.waypoints }
    );
    return res;
  } catch (e) {
    // fallback to client-side
    const distanceKm = routeLengthKm(route);
    const estMinutes = Math.round(distanceKm * 4);
    return { distanceKm, estMinutes, points: route.waypoints.length };
  }
}
