import { useMemo, useState } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { HARARE_CENTER } from "../../lib/dataset";

const DEFAULT_HOTSPOTS = [
  { id: 1, name: "CBD Junction", riskScore: 0.92, lat: -17.8278, lng: 31.0535 },
  { id: 2, name: "Mbare East", riskScore: 0.84, lat: -17.8332, lng: 31.0568 },
  { id: 3, name: "Kuwadzana Loop", riskScore: 0.72, lat: -17.8207, lng: 31.0654 },
];

const DEFAULT_INCIDENTS = [
  { id: 10, description: "Suspicious vehicle", severity: "HIGH", location: "Harare CBD", lat: -17.8292, lng: 31.0522 },
  { id: 11, description: "Street robbery", severity: "MEDIUM", location: "Mbare", lat: -17.8338, lng: 31.0584 },
];

function toSafeNumber(value, fallback = 0) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function normalizeSeverity(severity = "MEDIUM") {
  return String(severity ?? "MEDIUM").toUpperCase();
}

function resolveSeverityColor(severity = "MEDIUM") {
  const normalized = normalizeSeverity(severity);
  if (normalized === "HIGH" || normalized === "CRITICAL") return "#ef4444";
  if (normalized === "MEDIUM") return "#f59e0b";
  if (normalized === "LOW") return "#10b981";
  return "#60a5fa";
}

function resolveHotspotColor(riskScore = 0.5) {
  const normalizedScore = toSafeNumber(riskScore, 0.5);
  if (normalizedScore >= 0.85) return "#ef4444";
  if (normalizedScore >= 0.7) return "#f59e0b";
  return "#10b981";
}

function resolveRadius(value, base, min = 4, max = 16) {
  return Math.max(min, Math.min(max, toSafeNumber(value, base)));
}

export default function CrimeMap({ hotspots = [], incidents = [], patrolRoute }) {
  const [selectedFeature, setSelectedFeature] = useState(null);

  const hotspotMarkers = useMemo(() => {
    const source = hotspots.length ? hotspots : DEFAULT_HOTSPOTS;
    return source.map((hotspot, index) => ({
      ...hotspot,
      id: hotspot.id ?? `hotspot-${index + 1}`,
      name: hotspot.name ?? hotspot.dominant_category ?? `Hotspot ${index + 1}`,
      lat: hotspot.lat ?? hotspot.latitude ?? hotspot.location_lat ?? hotspot.centroid?.lat ?? HARARE_CENTER[0],
      lng: hotspot.lng ?? hotspot.longitude ?? hotspot.location_lng ?? hotspot.centroid?.lng ?? HARARE_CENTER[1],
      riskScore: toSafeNumber(hotspot.riskScore ?? hotspot.risk_score ?? hotspot.risk ?? 0.5, 0.5),
      threatLevel: hotspot.threatLevel ?? hotspot.severity ?? (toSafeNumber(hotspot.riskScore ?? hotspot.risk_score ?? hotspot.risk ?? 0.5, 0.5) >= 0.8 ? "HIGH" : "MEDIUM"),
    }));
  }, [hotspots]);

  const incidentMarkers = useMemo(() => {
    const source = incidents.length ? incidents : DEFAULT_INCIDENTS;
    return source.map((incident) => ({
      ...incident,
      lat: incident.lat ?? incident.latitude ?? incident.location_lat ?? HARARE_CENTER[0],
      lng: incident.lng ?? incident.longitude ?? incident.location_lng ?? HARARE_CENTER[1],
      severity: normalizeSeverity(incident.severity),
      locationLabel: incident.location_description || incident.location || "Harare district",
    }));
  }, [incidents]);

  const routeLayers = useMemo(() => {
    const routes = [];

    if (patrolRoute?.dijkstra?.waypoints?.length) {
      routes.push({ key: "dijkstra", label: patrolRoute.dijkstra.label || "Dijkstra route", color: "#3b82f6", points: patrolRoute.dijkstra.waypoints });
    }

    if (patrolRoute?.genetic?.waypoints?.length) {
      routes.push({ key: "genetic", label: patrolRoute.genetic.label || "Genetic route", color: "#10b981", points: patrolRoute.genetic.waypoints });
    }

    if (!routes.length && patrolRoute?.waypoints?.length) {
      routes.push({ key: "route", label: patrolRoute.label || "Patrol route", color: "#2ec4b6", points: patrolRoute.waypoints });
    }

    if (!routes.length) {
      routes.push({ key: "fallback", label: "Fallback route", color: "#2ec4b6", points: [[-17.8292, 31.0522], [-17.8238, 31.058], [-17.8207, 31.0654]] });
    }

    return routes;
  }, [patrolRoute]);

  return (
    <section className="panel map-panel">
      <div className="panel-heading">
        <p className="eyebrow">Live geospatial view</p>
        <h2>Threat landscape</h2>
      </div>
      <div className="map-surface">
        <MapContainer center={HARARE_CENTER} zoom={13} scrollWheelZoom className="leaflet-map">
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {routeLayers.map((route) => (
            <Polyline
              key={route.key}
              positions={route.points}
              pathOptions={{ color: route.color, weight: 4, dashArray: route.key === "fallback" ? "6 6" : "4 4" }}
            />
          ))}

          {hotspotMarkers.map((hotspot) => (
            <CircleMarker
              key={hotspot.id}
              center={[hotspot.lat, hotspot.lng]}
              radius={resolveRadius(hotspot.riskScore * 20, 10, 8, 18)}
              pathOptions={{ color: resolveHotspotColor(hotspot.riskScore), fillColor: resolveHotspotColor(hotspot.riskScore), fillOpacity: 0.75 }}
              eventHandlers={{
                click: () => setSelectedFeature({
                  kind: "hotspot",
                  title: hotspot.name,
                  subtitle: hotspot.dominant_category || "Threat hotspot",
                  details: [
                    { label: "Risk", value: `${Number(hotspot.riskScore).toFixed(2)}` },
                    { label: "Incidents", value: hotspot.incident_count || hotspot.incidents || "Tracked" },
                    { label: "Location", value: `${hotspot.lat.toFixed(4)}, ${hotspot.lng.toFixed(4)}` },
                  ],
                }),
              }}
            >
              <Popup>
                <strong>{hotspot.name}</strong>
                <br />
                Threat level: {hotspot.threatLevel || "MEDIUM"}
                <br />
                Risk score: {Number(hotspot.riskScore).toFixed(2)}
              </Popup>
            </CircleMarker>
          ))}

          {incidentMarkers.map((incident) => (
            <CircleMarker
              key={incident.id}
              center={[incident.lat, incident.lng]}
              radius={resolveRadius(incident.severity === "HIGH" || incident.severity === "CRITICAL" ? 9 : 6, 6, 5, 11)}
              pathOptions={{ color: resolveSeverityColor(incident.severity), fillColor: resolveSeverityColor(incident.severity), fillOpacity: 0.9 }}
              eventHandlers={{
                click: () => setSelectedFeature({
                  kind: "incident",
                  title: incident.locationLabel,
                  subtitle: incident.description,
                  details: [
                    { label: "Severity", value: incident.severity },
                    { label: "Category", value: incident.category || "General" },
                    { label: "Location", value: `${incident.lat.toFixed(4)}, ${incident.lng.toFixed(4)}` },
                  ],
                }),
              }}
            >
              <Popup>
                <strong>{incident.locationLabel}</strong>
                <br />
                {incident.description}
                <br />
                Severity: {incident.severity}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      <div style={{ marginTop: "0.8rem", padding: "0.85rem", borderRadius: "0.85rem", background: "#0f172a", color: "#e2e8f0", border: "1px solid rgba(255,255,255,0.14)" }}>
        {selectedFeature ? (
          <>
            <div style={{ fontSize: "0.75rem", color: "#7dd3fc", textTransform: "uppercase", letterSpacing: "0.16em" }}>{selectedFeature.kind}</div>
            <div style={{ fontWeight: 700, marginTop: "0.2rem" }}>{selectedFeature.title}</div>
            <div style={{ color: "#cbd5e1", marginTop: "0.2rem" }}>{selectedFeature.subtitle}</div>
            <div style={{ display: "grid", gap: "0.3rem", marginTop: "0.6rem" }}>
              {selectedFeature.details.map((detail) => (
                <div key={detail.label} style={{ display: "flex", justifyContent: "space-between", gap: "1rem", fontSize: "0.92rem" }}>
                  <span style={{ color: "#94a3b8" }}>{detail.label}</span>
                  <span style={{ fontWeight: 600 }}>{detail.value}</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ color: "#cbd5e1" }}>Click a marker to inspect the incident or hotspot details.</div>
        )}
      </div>

      <div className="legend-row">
        <span><i className="legend-dot hotspot" />Hotspot</span>
        <span><i className="legend-dot incident" />Incident</span>
        <span><i className="legend-dot route" />Route</span>
      </div>
    </section>
  );
}
