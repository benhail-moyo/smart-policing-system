"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/client";
import { CRIME_TYPES } from "@/lib/crime";
import {
  Siren,
  MapPin,
  Loader2,
  Send,
  AlertTriangle,
  Clock,
  ArrowRight,
} from "lucide-react";

const CrimeMap = dynamic(() => import("@/components/CrimeMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-slate-400">
      Loading map…
    </div>
  ),
});

type TriageResult = {
  priority: string;
  score: number;
  recommendation: string;
  eta: string;
};

const PRIORITY_BADGE: Record<string, string> = {
  critical: "bg-red-600",
  high: "bg-orange-500",
  medium: "bg-yellow-500 text-slate-900",
  low: "bg-green-600",
};

const PRIORITY_ICON: Record<string, React.ReactNode> = {
  critical: <AlertTriangle className="h-4 w-4 text-red-300" />,
  high: <AlertTriangle className="h-4 w-4 text-orange-300" />,
  medium: <AlertTriangle className="h-4 w-4 text-yellow-300" />,
  low: <AlertTriangle className="h-4 w-4 text-green-300" />,
};

function ReportInner() {
  const [type, setType] = useState<string>(CRIME_TYPES[0]);
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState(3);
  const [suburb, setSuburb] = useState("");
  const [point, setPoint] = useState<{ lat: number; lng: number } | null>(
    null
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TriageResult | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!point) {
      setError("Click on the map to set the incident location.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api<{ triage: TriageResult }>("/api/incidents", {
        method: "POST",
        body: JSON.stringify({
          type,
          description,
          severity,
          suburb,
          lat: point.lat,
          lng: point.lng,
        }),
      });
      setResult(res.triage);
      setDescription("");
      setSuburb("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid h-full grid-rows-[auto_1fr] gap-0 lg:grid-cols-[420px_1fr] lg:grid-rows-1">
      <div className="overflow-auto border-b border-slate-800 p-5 lg:border-b-0 lg:border-r">
        <h1 className="flex items-center gap-2 text-xl font-bold">
          <Siren className="h-5 w-5 text-red-400" />
          Report an Incident
        </h1>
        <p className="mb-4 text-sm text-slate-400">
          Fill in the details and click the map to set the location.
        </p>

        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              Crime type
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm"
            >
              {CRIME_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={3}
              placeholder="What happened?"
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              Suburb / area
            </label>
            <input
              value={suburb}
              onChange={(e) => setSuburb(e.target.value)}
              placeholder="e.g. CBD, Mbare"
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              Severity: {severity}/5
            </label>
            <input
              type="range"
              min={1}
              max={5}
              value={severity}
              onChange={(e) => setSeverity(Number(e.target.value))}
              className="w-full accent-red-500"
            />
          </div>

          <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950/50 px-3 py-2 text-xs text-slate-400">
            <MapPin className="h-3.5 w-3.5" />
            {point
              ? `Location: ${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}`
              : "Click the map to set location"}
          </div>

          {error && (
            <div className="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 py-2.5 text-sm font-semibold hover:bg-red-500 disabled:opacity-50"
          >
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            {submitting ? "Submitting…" : "Submit Report"}
          </button>
        </form>

        {result && (
          <div className="mt-5 rounded-xl border border-slate-700 bg-slate-900 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Triage Result</h2>
              <span
                className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold uppercase text-white ${
                  PRIORITY_BADGE[result.priority] ?? "bg-slate-600"
                }`}
              >
                {PRIORITY_ICON[result.priority] ?? null}
                {result.priority}
              </span>
            </div>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-400">Triage score</dt>
                <dd className="font-semibold">{result.score}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="flex items-center gap-1.5 text-slate-400">
                  <Clock className="h-3.5 w-3.5" />
                  Estimated response
                </dt>
                <dd className="font-semibold">{result.eta}</dd>
              </div>
              <div>
                <dt className="mb-1 flex items-center gap-1.5 text-slate-400">
                  <ArrowRight className="h-3.5 w-3.5" />
                  Recommended action
                </dt>
                <dd className="text-slate-200">{result.recommendation}</dd>
              </div>
            </dl>
          </div>
        )}
      </div>

      <div className="min-h-[350px]">
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

export default function ReportPage() {
  return (
    <AppShell>
      <ReportInner />
    </AppShell>
  );
}
