/**
 * CrimeMap — Leaflet map component (mirrors prototype CrimeMap.tsx).
 *
 * Uses raw Leaflet (not react-leaflet) for full control, matching the
 * prototype's dynamic import + useRef pattern exactly.
 *
 * Props:
 *   incidents   – array of { id, type, description, lat, lng, severity, priority, status, suburb, created_at }
 *   hotspots    – array of { id, lat, lng, count, weight, radius, level, top_types }
 *   routes      – array of { id, name, color, waypoints: [{lat,lng}] }
 *   onMapClick  – (lat, lng) => void   — for location selection
 *   selected    – { lat, lng } | null  — selected pin marker
 *   showIncidents – bool
 *   height      – CSS height string (default "100%")
 */
import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import { HARARE_CENTER, PRIORITY_COLOR, LEVEL_COLOR, SEVERITY_COLOR } from "../../lib/crime";

// Priority badge colours (prototype exact)
const getPriorityColor = (priority) =>
  PRIORITY_COLOR[priority?.toLowerCase()] ?? "#94a3b8";

// Hotspot ring colour
const getLevelColor = (level) =>
  LEVEL_COLOR[level?.toLowerCase()] ?? "#eab308";

// Backend severity → colour (HIGH / MEDIUM / LOW)
const getSeverityColor = (severity) =>
  SEVERITY_COLOR[severity?.toUpperCase()] ?? "#94a3b8";

export default function CrimeMap({
  incidents = [],
  hotspots  = [],
  routes    = [],
  onMapClick,
  selected,
  showIncidents = true,
  height = "100%",
}) {
  const containerRef = useRef(null);
  const mapRef       = useRef(null);
  const layerRef     = useRef(null);
  const selectRef    = useRef(null);
  const LRef         = useRef(null);
  const clickRef     = useRef(onMapClick);
  clickRef.current = onMapClick;

  // ── Init map once ─────────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default ?? (await import("leaflet"));
      if (cancelled || !containerRef.current || mapRef.current) return;
      LRef.current = L;

      const map = L.map(containerRef.current, {
        center: [HARARE_CENTER.lat, HARARE_CENTER.lng],
        zoom: 12,
        zoomControl: true,
      });

      L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }
      ).addTo(map);

      map.on("click", (e) => {
        clickRef.current?.(e.latlng.lat, e.latlng.lng);
      });

      layerRef.current = L.layerGroup().addTo(map);
      mapRef.current   = map;
      setTimeout(() => map.invalidateSize(), 150);
    })();

    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // ── Redraw layers when data changes ─────────────────────────────────────
  useEffect(() => {
    const L     = LRef.current;
    const layer = layerRef.current;
    if (!L || !layer) return;
    layer.clearLayers();

    // 1. Patrol routes (polylines drawn first, sit under markers)
    for (const r of routes) {
      const latlngs = r.waypoints.map((w) => [w.lat, w.lng]);
      L.polyline(latlngs, { color: r.color, weight: 5, opacity: 0.85 })
        .bindPopup(`<b>${r.name}</b>`)
        .addTo(layer);
      r.waypoints.forEach((w) => {
        L.circleMarker([w.lat, w.lng], {
          radius: 4,
          color: r.color,
          fillColor: r.color,
          fillOpacity: 1,
          weight: 1,
        }).addTo(layer);
      });
    }

    // 2. Hotspots (coloured risk circles from GIS module)
    for (const h of hotspots) {
      // Resolve coordinates — handle both adapted shape and raw backend shape
      const lat = h.lat ?? h.centroid?.lat ?? null;
      const lng = h.lng ?? h.centroid?.lng ?? null;
      if (!lat || !lng) continue;

      // Support both prototype field names (level) and backend field names (risk_score)
      const level = h.level ?? (
        (h.risk_score ?? h.riskScore ?? h.weight ?? 0) >= 0.7  ? "high"
        : (h.risk_score ?? h.riskScore ?? h.weight ?? 0) >= 0.45 ? "medium"
        : "low"
      );
      const color  = getLevelColor(level);
      const radius = h.radius ?? Math.min(1200, 350 + (h.incident_count ?? h.count ?? 1) * 60);
      const count  = h.count ?? h.incident_count ?? 0;
      const weight = h.weight ?? h.risk_score ?? h.riskScore ?? 0;
      const topTypes = h.topTypes ?? h.top_types ?? [];

      L.circle([lat, lng], {
        radius,
        color,
        fillColor: color,
        fillOpacity: 0.25,
        weight: 2,
      })
        .bindPopup(
          `<div style="min-width:180px;font-family:sans-serif">
            <b style="color:${color}">${level.toUpperCase()} Risk Hotspot</b><br/>
            <table style="width:100%;margin-top:6px;font-size:12px">
              <tr><td style="color:#64748b">Incidents</td><td><b>${count}</b></td></tr>
              <tr><td style="color:#64748b">Risk score</td><td><b>${typeof weight === "number" ? weight.toFixed(3) : weight}</b></td></tr>
              <tr><td style="color:#64748b">Category</td><td>${(Array.isArray(topTypes) ? topTypes.join(", ") : topTypes) || "—"}</td></tr>
            </table>
          </div>`
        )
        .addTo(layer);
    }

    // 3. Incidents (small dots, colour by priority/severity)
    if (showIncidents) {
      for (const i of incidents) {
        // Support both prototype priority field and backend severity field
        const color = i.priority
          ? getPriorityColor(i.priority)
          : getSeverityColor(i.severity);

        // Resolve coordinates from both adapted and raw backend shapes
        const lat = i.lat ?? i.location?.lat ?? i.latitude ?? i.location_lat;
        const lng = i.lng ?? i.location?.lng ?? i.longitude ?? i.location_lng;
        if (!lat || !lng) continue;

        const category  = i.type ?? i.category ?? "Incident";
        const severity  = i.severity ?? "";
        const suburb    = i.suburb ?? i.location_description ?? "";
        const summary   = i.description ?? i.triage_summary ?? i.raw_text ?? "";

        L.circleMarker([lat, lng], {
          radius: 6,
          color: "#0f172a",
          weight: 1,
          fillColor: color,
          fillOpacity: 0.95,
        })
          .bindPopup(
            `<div style="min-width:200px;font-family:sans-serif">
              <b>${category}</b>
              <span style="color:${color};font-weight:700"> ${severity ? '· ' + severity : ''}</span><br/>
              <span style="font-size:12px;color:#64748b">${suburb}</span><br/>
              <p style="margin:6px 0 0;font-size:12px;line-height:1.5">${summary.slice(0, 120)}${summary.length > 120 ? '…' : ''}</p>
            </div>`
          )
          .addTo(layer);
      }
    }
  }, [incidents, hotspots, routes, showIncidents]);

  // ── Selected pin (for incident reporting) ────────────────────────────────
  useEffect(() => {
    const L   = LRef.current;
    const map = mapRef.current;
    if (!L || !map) return;

    if (selectRef.current) {
      map.removeLayer(selectRef.current);
      selectRef.current = null;
    }

    if (selected) {
      const icon = L.divIcon({
        className: "",
        html: `<div style="width:24px;height:30px;transform:translate(-12px,-30px)">
          <svg viewBox="0 0 24 30" width="24" height="30">
            <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 18 12 18s12-9 12-18C24 5.4 18.6 0 12 0z" fill="#ef4444" stroke="#b91c1c" stroke-width="1.5"/>
            <circle cx="12" cy="11" r="4" fill="white" opacity="0.9"/>
          </svg>
        </div>`,
        iconSize: [0, 0],
      });
      selectRef.current = L.marker([selected.lat, selected.lng], { icon })
        .addTo(map)
        .bindPopup("Selected incident location")
        .openPopup();
    }
  }, [selected]);

  return (
    <div ref={containerRef} style={{ height, width: "100%" }} />
  );
}
