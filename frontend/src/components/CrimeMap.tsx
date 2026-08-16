"use client";

import { useEffect, useRef, useState } from "react";
import "leaflet/dist/leaflet.css";
import type * as LeafletNS from "leaflet";
import { HARARE_CENTER } from "@/lib/crime";

export type MapIncident = {
  id: number;
  type: string;
  description: string;
  lat: number;
  lng: number;
  severity: number;
  priority: string;
  status: string;
  suburb?: string | null;
  createdAt?: string;
};

export type MapHotspot = {
  id: number;
  lat: number;
  lng: number;
  count: number;
  weight: number;
  radius: number;
  level: string;
  topTypes?: string[] | null;
};

export type MapRoute = {
  id: string;
  name: string;
  color: string;
  waypoints: { lat: number; lng: number }[];
  geometry?: {
    type: string;
    coordinates: [number, number][];
  };
};

export type MapDeployment = {
  id: number;
  unitType: "foot" | "vehicle";
  areaName: string;
  lat: number;
  lng: number;
  instructions?: string;
  status?: string;
};

const PRIORITY_COLOR: Record<string, string> = {
  critical: "#dc2626",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
};

const LEVEL_COLOR: Record<string, string> = {
  high: "#dc2626",
  medium: "#f97316",
  low: "#eab308",
};

export default function CrimeMap({
  incidents = [],
  hotspots = [],
  routes = [],
  deployments = [],
  routeSelection = [],
  onMapClick,
  selected,
  showIncidents = true,
  height = "100%",
}: {
  incidents?: MapIncident[];
  hotspots?: MapHotspot[];
  routes?: MapRoute[];
  deployments?: MapDeployment[];
  routeSelection?: { lat: number; lng: number }[];
  onMapClick?: (lat: number, lng: number) => void;
  selected?: { lat: number; lng: number } | null;
  showIncidents?: boolean;
  height?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletNS.Map | null>(null);
  const layerRef = useRef<LeafletNS.LayerGroup | null>(null);
  const selectRef = useRef<LeafletNS.Layer | null>(null);
  const LRef = useRef<typeof LeafletNS | null>(null);
  const clickRef = useRef(onMapClick);
  const [mapReady, setMapReady] = useState(false);
  clickRef.current = onMapClick;

  // init map once
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const L = (await import("leaflet")).default ?? (await import("leaflet"));
      if (cancelled || !containerRef.current || mapRef.current) return;
      LRef.current = L as typeof LeafletNS;

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

      map.on("click", (e: LeafletNS.LeafletMouseEvent) => {
        clickRef.current?.(e.latlng.lat, e.latlng.lng);
      });

      layerRef.current = L.layerGroup().addTo(map);
      mapRef.current = map;
      setMapReady(true);
      // force size recalc
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

  // redraw layers when data changes
  useEffect(() => {
    const L = LRef.current;
    const layer = layerRef.current;
    if (!L || !layer) return;
    layer.clearLayers();

    // routes (polylines) — drawn first so they sit under markers
    for (const r of routes) {
      // Use GeoJSON geometry if available, otherwise fall back to waypoints
      let latlngs: [number, number][];
      if (r.geometry && r.geometry.type === "LineString" && r.geometry.coordinates.length > 0) {
        // GeoJSON coordinates are [lng, lat], Leaflet expects [lat, lng]
        latlngs = r.geometry.coordinates.map(
          (coord) => [coord[1], coord[0]] as [number, number]
        );
      } else if (r.waypoints && r.waypoints.length > 0) {
        // Fall back to waypoints (for hotspot-based routes)
        latlngs = r.waypoints.map(
          (w) => [w.lat, w.lng] as [number, number]
        );
      } else {
        continue; // Skip routes with no geometry or waypoints
      }
      
      L.polyline(latlngs, {
        color: r.color,
        weight: 5,
        opacity: 0.85,
      })
        .bindPopup(`<b>${r.name}</b>`)
        .addTo(layer);
      
      // waypoint dots only if we have waypoints (not for road network routes)
      if (r.waypoints && r.waypoints.length > 0) {
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
    }

    // hotspots (colored circles)
    for (const h of hotspots) {
      const color = LEVEL_COLOR[h.level] ?? "#eab308";
      L.circle([h.lat, h.lng], {
        radius: h.radius,
        color,
        fillColor: color,
        fillOpacity: 0.28,
        weight: 2,
      })
        .bindPopup(
          `<div style="min-width:170px">
            <b>${h.level.toUpperCase()} Risk Hotspot</b><br/>
            Incidents: <b>${h.count}</b><br/>
            Risk score: <b>${h.weight}</b><br/>
            Common: ${
              (h.topTypes ?? []).join(", ") || "n/a"
            }
          </div>`
        )
        .addTo(layer);
    }

    // incidents (small dots)
    if (showIncidents) {
      for (const i of incidents) {
        const color = PRIORITY_COLOR[i.priority] ?? "#94a3b8";
        L.circleMarker([i.lat, i.lng], {
          radius: 5,
          color: "#0f172a",
          weight: 1,
          fillColor: color,
          fillOpacity: 0.95,
        })
          .bindPopup(
            `<div style="min-width:170px">
              <b>${i.type}</b> <span style="color:${color}">(${i.priority})</span><br/>
              ${i.description}<br/>
              <small>${i.suburb ?? ""} · severity ${i.severity}/5 · ${
              i.status
            }</small>
            </div>`
          )
          .addTo(layer);
      }
    }

    for (const d of deployments) {
      const color = d.unitType === "foot" ? "#22c55e" : "#38bdf8";
      const symbol = d.unitType === "foot" ? "●" : "◆";
      L.circleMarker([d.lat, d.lng], { radius: 9, color: "#0f172a", weight: 2, fillColor: color, fillOpacity: 1 })
        .bindPopup(`<b>${symbol} ${d.unitType === "foot" ? "Foot" : "Vehicle"} deployment</b><br/>${d.areaName}<br/><small>${d.instructions || "No instructions"}</small>`)
        .addTo(layer);
    }

    for (const [index, point] of routeSelection.entries()) {
      const isStart = index === 0;
      L.circleMarker([point.lat, point.lng], {
        radius: 8,
        color: "#ffffff",
        weight: 2,
        fillColor: isStart ? "#22c55e" : "#f97316",
        fillOpacity: 1,
      })
        .bindTooltip(isStart ? "Patrol start" : `Stop ${index}`, { permanent: true, direction: "top" })
        .addTo(layer);
    }
  }, [incidents, hotspots, routes, deployments, routeSelection, showIncidents, mapReady]);

  // selected marker for reporting
  useEffect(() => {
    const L = LRef.current;
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

  return <div ref={containerRef} style={{ height, width: "100%" }} />;
}
