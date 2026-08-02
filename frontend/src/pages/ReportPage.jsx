/**
 * ReportPage — mirrors prototype app/report/page.tsx
 *
 * Two-panel layout:
 *  Left:  Incident form (type, description, suburb, severity, triage result)
 *  Right: Leaflet map to click-select incident location
 */
import { useState } from "react";
import {
  Siren, MapPin, Loader2, Send, AlertTriangle, Clock, ArrowRight,
} from "lucide-react";
import CrimeMap   from "../components/map/CrimeMap";
import { api }    from "../lib/client";
import { CRIME_TYPES } from "../lib/crime";

const API = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const PRIORITY_BADGE_CLASS = {
  critical: "badge-critical",
  high:     "badge-high",
  medium:   "badge-medium",
  low:      "badge-low",
  HIGH:     "badge-HIGH",
  MEDIUM:   "badge-MEDIUM",
  LOW:      "badge-LOW",
};

export default function ReportPage() {
  const [crimeType,    setCrimeType]    = useState(CRIME_TYPES[0]);
  const [description,  setDescription]  = useState("");
  const [severity,     setSeverity]     = useState(3);
  const [suburb,       setSuburb]       = useState("");
  const [point,        setPoint]        = useState(null);  // { lat, lng }
  const [submitting,   setSubmitting]   = useState(false);
  const [error,        setError]        = useState(null);
  const [result,       setResult]       = useState(null);  // triage result

  async function submit(e) {
    e.preventDefault();
    setError(null);

    if (!point) {
      setError("Click on the map to set the incident location.");
      return;
    }

    setSubmitting(true);
    try {
      // Backend POST /api/v1/incidents/ expects raw_text + location_lat/lng
      const rawText = `[${crimeType}] ${description}${suburb ? ` — ${suburb}` : ""}`;
      const res = await api(`${API}/incidents/`, {
        method: "POST",
        body: JSON.stringify({
          raw_text:             rawText,
          location_lat:         point.lat,
          location_lng:         point.lng,
          location_description: suburb,
        }),
      });

      // Adapt triage from backend response
      const t = res.triage ?? {};
      setResult({
        priority:       t.severity ?? t.priority ?? "medium",
        score:          t.confidence != null ? Math.round(t.confidence * 100) : 0,
        recommendation: t.summary ?? t.reasoning ?? "See response officer for details.",
        eta:            severityToEta(t.severity),
      });

      setDescription("");
      setSuburb("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  function severityToEta(severity) {
    const map = { HIGH: "5-15 min", MEDIUM: "15-45 min", LOW: "1-4 hrs", CRITICAL: "0-5 min" };
    return map[(severity ?? "").toUpperCase()] ?? "TBD";
  }

  const priorityKey = (result?.priority ?? "").toLowerCase();

  return (
    <div className="cw-report-layout">
      {/* Left panel — form */}
      <div className="cw-report-panel">
        <h1 className="cw-report-title">
          <Siren size={20} color="#f87171" />
          Report an Incident
        </h1>
        <p className="cw-report-sub">Fill in the details and click the map to set the location.</p>

        <form onSubmit={submit}>
          <div className="cw-form-group">
            <label className="cw-form-label">Crime type</label>
            <select
              value={crimeType}
              onChange={(e) => setCrimeType(e.target.value)}
              className="cw-form-select"
            >
              {CRIME_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="cw-form-group">
            <label className="cw-form-label">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              placeholder="What happened?"
              className="cw-form-textarea"
            />
          </div>

          <div className="cw-form-group">
            <label className="cw-form-label">Suburb / area</label>
            <input
              value={suburb}
              onChange={(e) => setSuburb(e.target.value)}
              placeholder="e.g. CBD, Mbare"
              className="cw-form-input"
            />
          </div>

          <div className="cw-form-group">
            <label className="cw-form-label">Severity: {severity}/5</label>
            <input
              type="range"
              min={1}
              max={5}
              value={severity}
              onChange={(e) => setSeverity(Number(e.target.value))}
              className="cw-range"
            />
          </div>

          <div className="cw-location-hint" style={{ marginBottom: "12px" }}>
            <MapPin size={14} />
            {point
              ? `Location: ${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}`
              : "Click the map to set location"}
          </div>

          {error && <div className="cw-error-box">{error}</div>}

          <button type="submit" disabled={submitting} className="cw-submit-btn">
            {submitting ? <Loader2 size={16} className="cw-spin" /> : <Send size={16} />}
            {submitting ? "Submitting…" : "Submit Report"}
          </button>
        </form>

        {/* Triage result */}
        {result && (
          <div className="cw-triage-card">
            <div className="cw-triage-header">
              <div className="cw-triage-title">Triage Result</div>
              <div className={`cw-priority-badge ${PRIORITY_BADGE_CLASS[priorityKey] ?? "badge-low"}`}>
                <AlertTriangle size={14} />
                {result.priority}
              </div>
            </div>
            <dl className="cw-triage-dl">
              <div className="cw-triage-row">
                <dt className="cw-triage-dt">Triage score</dt>
                <dd className="cw-triage-dd">{result.score}</dd>
              </div>
              <div className="cw-triage-row">
                <dt className="cw-triage-dt" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Clock size={14} />
                  Estimated response
                </dt>
                <dd className="cw-triage-dd">{result.eta}</dd>
              </div>
              <div>
                <dt className="cw-triage-dt" style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                  <ArrowRight size={14} />
                  Recommended action
                </dt>
                <dd style={{ color: "#e2e8f0" }}>{result.recommendation}</dd>
              </div>
            </dl>
          </div>
        )}
      </div>

      {/* Right panel — map */}
      <div style={{ minHeight: "350px" }}>
        <CrimeMap
          onMapClick={(lat, lng) => setPoint({ lat, lng })}
          selected={point}
          showIncidents={false}
          height="100%"
        />
      </div>
    </div>
  );
}
