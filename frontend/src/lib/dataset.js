export const HARARE_CENTER = [-17.8292, 31.0522];

const HARARE_ZONES = [
  { name: "Harare CBD", center: [-17.8292, 31.0522], radius: 0.015, categories: ["robbery", "fraud", "suspicious_activity"], severities: ["HIGH", "HIGH", "MEDIUM", "LOW"] },
  { name: "Mbare", center: [-17.8677, 31.0359], radius: 0.014, categories: ["robbery", "assault", "theft"], severities: ["HIGH", "HIGH", "MEDIUM", "LOW"] },
  { name: "Kuwadzana", center: [-17.8207, 31.0654], radius: 0.012, categories: ["domestic_dispute", "assault", "theft"], severities: ["MEDIUM", "MEDIUM", "LOW", "LOW"] },
  { name: "Budiriro", center: [-17.9100, 31.0200], radius: 0.013, categories: ["drug_offence", "theft", "vandalism"], severities: ["HIGH", "MEDIUM", "MEDIUM", "LOW"] },
  { name: "Highfields", center: [-17.8900, 31.0100], radius: 0.012, categories: ["drug_offence", "theft", "vandalism"], severities: ["HIGH", "MEDIUM", "MEDIUM", "LOW"] },
  { name: "Chitungwiza", center: [-18.0130, 31.0750], radius: 0.016, categories: ["robbery", "theft", "drug_offence"], severities: ["HIGH", "MEDIUM", "MEDIUM", "LOW"] },
];

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function buildHarareDataset(totalIncidents = 500) {
  const incidents = [];
  const perZone = Math.ceil(totalIncidents / HARARE_ZONES.length);

  HARARE_ZONES.forEach((zone, zoneIndex) => {
    for (let index = 0; index < perZone; index += 1) {
      const offsetLat = ((index * 17 + zoneIndex * 29) % 13 - 6) * 0.0012;
      const offsetLng = (((index + zoneIndex) * 11) % 15 - 7) * 0.0014;
      const jitterLat = Math.sin(index * 0.7 + zoneIndex) * 0.0008;
      const jitterLng = Math.cos(index * 0.4 + zoneIndex * 1.1) * 0.0009;
      const lat = zone.center[0] + offsetLat + jitterLat;
      const lng = zone.center[1] + offsetLng + jitterLng;
      const category = zone.categories[index % zone.categories.length];
      const severity = zone.severities[(index + zoneIndex) % zone.severities.length];
      const confidence = clamp(0.75 + (index % 10) * 0.02, 0.75, 0.98);

      incidents.push({
        id: `incident-${zoneIndex + 1}-${index + 1}`,
        raw_text: `Synthetic Harare GIS report in ${zone.name}: ${category.replace("_", " ")} reported near ${zone.name}`,
        description: `${category.replace("_", " ")} reported near ${zone.name}`,
        category,
        severity,
        triage_confidence: Number(confidence.toFixed(2)),
        triage_summary: `${category.replace("_", " ")} alert in ${zone.name}`,
        status: index % 4 === 0 ? "ASSIGNED" : "TRIAGED",
        location_description: zone.name,
        location: { lat, lng },
        lat,
        lng,
        created_at: new Date(Date.now() - index * 3600000).toISOString(),
      });
    }
  });

  const hotspots = HARARE_ZONES.map((zone, index) => ({
    id: index + 1,
    name: zone.name,
    dominant_category: zone.categories[0],
    incident_count: Math.max(18, perZone - index * 2),
    risk_score: Number(clamp(0.54 + index * 0.07 + (index % 2) * 0.04, 0.52, 0.95).toFixed(2)),
    centroid: { lat: zone.center[0], lng: zone.center[1] },
    lat: zone.center[0],
    lng: zone.center[1],
  }));

  const dijkstraRoute = {
    id: "dijkstra",
    label: "Dijkstra",
    color: "#3b82f6",
    distanceKm: 12.6,
    fuelLitres: 2.9,
    timeMinutes: 41,
    waypoints: hotspots.slice(0, 6).map((item) => [item.lat, item.lng]),
  };

  const geneticRoute = {
    id: "genetic",
    label: "Genetic Algorithm",
    color: "#10b981",
    distanceKm: 11.8,
    fuelLitres: 2.5,
    timeMinutes: 38,
    waypoints: hotspots.slice(0, 6).map((item, index) => [item.lat + index * 0.001, item.lng + index * 0.0012]),
  };

  return {
    incidents: incidents.slice(0, totalIncidents),
    hotspots,
    route: { dijkstra: dijkstraRoute, genetic: geneticRoute },
  };
}

export function normalizeIncident(raw, fallbackIndex = 0) {
  const location = raw?.location || raw?.centroid || raw?.coordinates || {};
  const lat = raw?.lat ?? raw?.latitude ?? location?.lat ?? location?.latitude ?? location?.y ?? null;
  const lng = raw?.lng ?? raw?.longitude ?? location?.lng ?? location?.longitude ?? location?.x ?? null;
  const description = raw?.raw_text || raw?.description || raw?.triage_summary || "Incident report";
  const category = raw?.category || raw?.dominant_category || "general";
  const severity = String(raw?.severity || "MEDIUM").toUpperCase();

  return {
    id: raw?.id ?? `incident-${fallbackIndex}`,
    raw_text: description,
    description,
    category,
    severity,
    triage_confidence: raw?.triage_confidence ?? null,
    triage_summary: raw?.triage_summary ?? `${category} alert`,
    status: raw?.status || "TRIAGED",
    location_description: raw?.location_description || "Harare district",
    location: location && typeof location === "object" ? location : { lat, lng },
    lat,
    lng,
    created_at: raw?.created_at || new Date().toISOString(),
  };
}

export function normalizeHotspot(raw, fallbackIndex = 0) {
  const centroid = raw?.centroid || raw?.location || raw?.center || {};
  const lat = raw?.lat ?? raw?.latitude ?? centroid?.lat ?? centroid?.latitude ?? centroid?.y ?? null;
  const lng = raw?.lng ?? raw?.longitude ?? centroid?.lng ?? centroid?.longitude ?? centroid?.x ?? null;

  return {
    id: raw?.id ?? `hotspot-${fallbackIndex}`,
    name: raw?.name || raw?.dominant_category || `Hotspot ${fallbackIndex + 1}`,
    dominant_category: raw?.dominant_category || raw?.category || "general",
    incident_count: raw?.incident_count || raw?.incidents || 0,
    risk_score: raw?.risk_score ?? raw?.riskScore ?? 0.5,
    centroid: centroid && typeof centroid === "object" ? centroid : { lat, lng },
    lat,
    lng,
  };
}

export function buildDashboardDataset(apiIncidents = [], apiHotspots = [], apiRoutes = null) {
  const fallback = buildHarareDataset(500);
  const rawIncidents = Array.isArray(apiIncidents) && apiIncidents.length ? apiIncidents : fallback.incidents;
  const normalizedIncidents = rawIncidents.map((item, index) => normalizeIncident(item, index));

  const augmentedIncidents = normalizedIncidents.length >= 500
    ? normalizedIncidents.slice(0, 500)
    : [...normalizedIncidents, ...fallback.incidents.slice(normalizedIncidents.length, 500 - normalizedIncidents.length).map((item, index) => normalizeIncident(item, normalizedIncidents.length + index))];

  const normalizedHotspots = (Array.isArray(apiHotspots) && apiHotspots.length ? apiHotspots : fallback.hotspots).map((item, index) => normalizeHotspot(item, index));
  const augmentedHotspots = normalizedHotspots.length >= 6
    ? normalizedHotspots.slice(0, 6)
    : [...normalizedHotspots, ...fallback.hotspots.slice(normalizedHotspots.length, 6 - normalizedHotspots.length).map((item, index) => normalizeHotspot(item, normalizedHotspots.length + index))];

  const route = apiRoutes?.dijkstra || apiRoutes?.genetic || fallback.route;
  const dijkstra = route?.dijkstra || fallback.route.dijkstra;
  const genetic = route?.genetic || fallback.route.genetic;

  return {
    incidents: augmentedIncidents,
    hotspots: augmentedHotspots,
    route: { dijkstra, genetic },
  };
}

export function buildStats(incidents = [], hotspots = []) {
  const bySeverity = { HIGH: 0, MEDIUM: 0, LOW: 0, CRITICAL: 0 };
  incidents.forEach((incident) => {
    const severity = String(incident.severity || "MEDIUM").toUpperCase();
    if (bySeverity[severity] !== undefined) {
      bySeverity[severity] += 1;
    }
  });

  return {
    totalIncidents: incidents.length,
    highSeverity: bySeverity.HIGH + bySeverity.CRITICAL,
    activeHotspots: hotspots.length,
    patrolCoverage: Math.max(3, hotspots.length),
    bySeverity,
  };
}
