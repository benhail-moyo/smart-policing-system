"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { api, getStoredUser } from "@/lib/client";
import { Search, Filter, FileText, Calendar, MapPin, AlertTriangle, Shield, CheckCircle2, Clock, Edit, X } from "lucide-react";

type Incident = {
  id: number;
  raw_text: string;
  category: string;
  severity: number;
  priority: string;
  triage_confidence: number;
  triage_summary: string;
  extracted_entities: {
    person_names: string[];
    vehicle_descriptions: string[];
    location_details: string[];
    weapon_descriptions: string[];
    time_details: string[];
    other_details: string[];
  };
  manual_severity: string | null;
  manual_category: string | null;
  override_reason: string | null;
  status: string;
  location: { lat: number; lng: number };
  suburb: string;
  location_description: string;
  reportedBy: string;
  created_at: string;
  occurred_at: string | null;
};

type FilterState = {
  category: string;
  severity: string;
  status: string;
  startDate: string;
  endDate: string;
  location: string;
  searchQuery: string;
};

function IncidentsInner() {
  const searchParams = useSearchParams();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filteredIncidents, setFilteredIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const user = getStoredUser();

  const [filters, setFilters] = useState<FilterState>({
    category: "all",
    severity: "all",
    status: "all",
    startDate: "",
    endDate: "",
    location: "",
    searchQuery: "",
  });

  const loadIncidents = async () => {
    try {
      const data = await api<{ incidents: Incident[] }>("/api/incidents/search");
      setIncidents(data.incidents);
      setFilteredIncidents(data.incidents);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load incidents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin" || user?.role === "officer") {
      loadIncidents();
    } else {
      setError("Access restricted to administrators and officers");
      setLoading(false);
    }
  }, [user]);

  // Handle ref parameter from map popup
  useEffect(() => {
    const refParam = searchParams.get("ref");
    if (refParam && !loading && incidents.length > 0) {
      const incidentId = parseInt(refParam);
      const incident = incidents.find(inc => inc.id === incidentId);
      if (incident) {
        setSelectedIncident(incident);
      }
    }
  }, [searchParams, incidents, loading]);

  useEffect(() => {
    let filtered = incidents;

    if (filters.category !== "all") {
      filtered = filtered.filter(inc => inc.category === filters.category);
    }

    if (filters.severity !== "all") {
      filtered = filtered.filter(inc => inc.priority === filters.severity);
    }

    if (filters.status !== "all") {
      filtered = filtered.filter(inc => inc.status === filters.status);
    }

    if (filters.location) {
      filtered = filtered.filter(inc => 
        inc.suburb.toLowerCase().includes(filters.location.toLowerCase()) ||
        inc.location_description?.toLowerCase().includes(filters.location.toLowerCase())
      );
    }

    if (filters.searchQuery) {
      filtered = filtered.filter(inc =>
        inc.raw_text.toLowerCase().includes(filters.searchQuery.toLowerCase()) ||
        inc.id.toString().includes(filters.searchQuery)
      );
    }

    if (filters.startDate) {
      filtered = filtered.filter(inc => new Date(inc.created_at) >= new Date(filters.startDate));
    }

    if (filters.endDate) {
      filtered = filtered.filter(inc => new Date(inc.created_at) <= new Date(filters.endDate));
    }

    setFilteredIncidents(filtered);
  }, [filters, incidents]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical": return "bg-red-500/15 text-red-300 border-red-500/30";
      case "high": return "bg-orange-500/15 text-orange-300 border-orange-500/30";
      case "medium": return "bg-yellow-500/15 text-yellow-300 border-yellow-500/30";
      case "low": return "bg-blue-500/15 text-blue-300 border-blue-500/30";
      default: return "bg-slate-500/15 text-slate-300 border-slate-500/30";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "reported": return "bg-yellow-500/15 text-yellow-300 border-yellow-500/30";
      case "dispatched": return "bg-blue-500/15 text-blue-300 border-blue-500/30";
      case "resolved": return "bg-green-500/15 text-green-300 border-green-500/30";
      default: return "bg-slate-500/15 text-slate-300 border-slate-500/30";
    }
  };

  const categories = Array.from(new Set(incidents.map(inc => inc.category)));

  if (loading) {
    return (
      <div className="min-h-full bg-slate-950 p-4 md:p-7">
        <div className="flex h-full items-center justify-center text-slate-400">
          Loading incidents...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-full bg-slate-950 p-4 md:p-7">
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-red-200">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-slate-950 p-4 md:p-7">
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-2 text-cyan-300">
          <FileText className="h-5 w-5" />
          <span className="text-xs font-bold uppercase tracking-[0.24em]">
            Incident Management
          </span>
        </div>
        <h1 className="text-3xl font-bold">Incidents</h1>
        <p className="mt-1 text-sm text-slate-400">
          View and manage all reported incidents with full details and triage information
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div className="flex flex-1 items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search incidents by ID or content..."
            value={filters.searchQuery}
            onChange={(e) => setFilters({ ...filters, searchQuery: e.target.value })}
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-400 outline-none"
          />
        </div>

        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700"
        >
          <Filter className="h-4 w-4" />
          Filters
        </button>
      </div>

      {showFilters && (
        <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
            <div>
              <label className="mb-1 block text-xs text-slate-400">Category</label>
              <select
                value={filters.category}
                onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
              >
                <option value="all">All Categories</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-400">Priority</label>
              <select
                value={filters.severity}
                onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
              >
                <option value="all">All Priorities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-400">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
              >
                <option value="all">All Statuses</option>
                <option value="reported">Reported</option>
                <option value="dispatched">Dispatched</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-400">Location</label>
              <input
                type="text"
                placeholder="Suburb or area"
                value={filters.location}
                onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-400">Start Date</label>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-400">End Date</label>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>
      )}

      <div className="mb-4 text-sm text-slate-400">
        Showing {filteredIncidents.length} of {incidents.length} incidents
      </div>

      {/* Incidents Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs font-semibold uppercase text-slate-400">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Location</th>
              <th className="px-4 py-3">Reported</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredIncidents.map((incident) => (
              <tr 
                key={incident.id} 
                className="border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer"
                onClick={() => setSelectedIncident(incident)}
              >
                <td className="px-4 py-3 text-sm font-mono text-slate-300">
                  #{incident.id}
                </td>
                <td className="px-4 py-3 text-sm">
                  {incident.category}
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${getPriorityColor(incident.priority)}`}>
                    {incident.priority}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${getStatusColor(incident.status)}`}>
                    {incident.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-slate-300">
                  {incident.suburb}
                </td>
                <td className="px-4 py-3 text-sm text-slate-400">
                  {new Date(incident.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedIncident(incident);
                    }}
                    className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/20"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredIncidents.length === 0 && (
          <div className="p-8 text-center text-slate-400">
            No incidents match the current filters
          </div>
        )}
      </div>

      {/* Incident Detail Modal */}
      {selectedIncident && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => setSelectedIncident(null)}
        >
          <div 
            className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-slate-800 bg-slate-900 p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold">Incident #{selectedIncident.id}</h2>
              <button
                onClick={() => setSelectedIncident(null)}
                className="rounded-lg p-2 hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Original Report */}
            <div className="mb-6 rounded-xl border border-slate-800 bg-slate-800/50 p-4">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <FileText className="h-4 w-4 text-cyan-400" />
                Original Report
              </h3>
              <p className="text-sm text-slate-300">{selectedIncident.raw_text}</p>
            </div>

            {/* NLP Processed Report */}
            <div className="mb-6 rounded-xl border border-slate-800 bg-slate-800/50 p-4">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <Shield className="h-4 w-4 text-cyan-400" />
                NLP Triage Analysis
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <div className="text-xs text-slate-400">Category</div>
                  <div className="text-sm font-semibold">{selectedIncident.category}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Priority</div>
                  <div className="text-sm font-semibold">{selectedIncident.priority}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Confidence</div>
                  <div className="text-sm font-semibold">{(selectedIncident.triage_confidence * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Status</div>
                  <div className="text-sm font-semibold">{selectedIncident.status}</div>
                </div>
              </div>
              <div className="mt-4">
                <div className="text-xs text-slate-400">Triage Summary</div>
                <div className="text-sm text-slate-300">{selectedIncident.triage_summary}</div>
              </div>
            </div>

            {/* Extracted Entities */}
            <div className="mb-6 rounded-xl border border-slate-800 bg-slate-800/50 p-4">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <AlertTriangle className="h-4 w-4 text-cyan-400" />
                Extracted Entities
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                {selectedIncident.extracted_entities.person_names?.length > 0 && (
                  <div>
                    <div className="text-xs text-slate-400">Person Names</div>
                    <div className="text-sm text-slate-300">
                      {selectedIncident.extracted_entities.person_names.join(", ")}
                    </div>
                  </div>
                )}
                {selectedIncident.extracted_entities.vehicle_descriptions?.length > 0 && (
                  <div>
                    <div className="text-xs text-slate-400">Vehicle Descriptions</div>
                    <div className="text-sm text-slate-300">
                      {selectedIncident.extracted_entities.vehicle_descriptions.join(", ")}
                    </div>
                  </div>
                )}
                {selectedIncident.extracted_entities.location_details?.length > 0 && (
                  <div>
                    <div className="text-xs text-slate-400">Location Details</div>
                    <div className="text-sm text-slate-300">
                      {selectedIncident.extracted_entities.location_details.join(", ")}
                    </div>
                  </div>
                )}
                {selectedIncident.extracted_entities.weapon_descriptions?.length > 0 && (
                  <div>
                    <div className="text-xs text-slate-400">Weapon Descriptions</div>
                    <div className="text-sm text-slate-300">
                      {selectedIncident.extracted_entities.weapon_descriptions.join(", ")}
                    </div>
                  </div>
                )}
                {selectedIncident.extracted_entities.time_details?.length > 0 && (
                  <div>
                    <div className="text-xs text-slate-400">Time Details</div>
                    <div className="text-sm text-slate-300">
                      {selectedIncident.extracted_entities.time_details.join(", ")}
                    </div>
                  </div>
                )}
                {selectedIncident.extracted_entities.other_details?.length > 0 && (
                  <div>
                    <div className="text-xs text-slate-400">Other Details</div>
                    <div className="text-sm text-slate-300">
                      {selectedIncident.extracted_entities.other_details.join(", ")}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Override Information */}
            {selectedIncident.manual_severity || selectedIncident.manual_category ? (
              <div className="mb-6 rounded-xl border border-orange-500/30 bg-orange-500/10 p-4">
                <h3 className="mb-2 flex items-center gap-2 font-semibold">
                  <Edit className="h-4 w-4 text-orange-400" />
                  Manual Override Applied
                </h3>
                <div className="grid gap-4 md:grid-cols-2">
                  {selectedIncident.manual_severity && (
                    <div>
                      <div className="text-xs text-slate-400">Override Severity</div>
                      <div className="text-sm font-semibold">{selectedIncident.manual_severity}</div>
                    </div>
                  )}
                  {selectedIncident.manual_category && (
                    <div>
                      <div className="text-xs text-slate-400">Override Category</div>
                      <div className="text-sm font-semibold">{selectedIncident.manual_category}</div>
                    </div>
                  )}
                </div>
                {selectedIncident.override_reason && (
                  <div className="mt-4">
                    <div className="text-xs text-slate-400">Override Reason</div>
                    <div className="text-sm text-slate-300">{selectedIncident.override_reason}</div>
                  </div>
                )}
              </div>
            ) : (
              <div className="mb-6 rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-4">
                <h3 className="mb-2 flex items-center gap-2 font-semibold">
                  <Edit className="h-4 w-4 text-cyan-400" />
                  Override Triage Assessment
                </h3>
                <p className="mb-4 text-sm text-slate-400">
                  Officers and administrators can override the NLP triage assessment if needed.
                </p>
                <OverrideForm incident={selectedIncident} onUpdate={() => {
                  // Refresh incident data
                  setSelectedIncident(null);
                }} onReload={loadIncidents} />
              </div>
            )}

            {/* Incident Details */}
            <div className="mb-6 rounded-xl border border-slate-800 bg-slate-800/50 p-4">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <MapPin className="h-4 w-4 text-cyan-400" />
                Incident Details
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <div className="text-xs text-slate-400">Location</div>
                  <div className="text-sm text-slate-300">{selectedIncident.suburb}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Coordinates</div>
                  <div className="text-sm text-slate-300">
                    {selectedIncident.location.lat.toFixed(4)}, {selectedIncident.location.lng.toFixed(4)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Reported By</div>
                  <div className="text-sm text-slate-300">{selectedIncident.reportedBy}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Reported At</div>
                  <div className="text-sm text-slate-300">
                    {new Date(selectedIncident.created_at).toLocaleString()}
                  </div>
                </div>
                {selectedIncident.occurred_at && (
                  <div>
                    <div className="text-xs text-slate-400">Occurred At</div>
                    <div className="text-sm text-slate-300">
                      {new Date(selectedIncident.occurred_at).toLocaleString()}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function OverrideForm({ incident, onUpdate, onReload }: { incident: Incident; onUpdate: () => void; onReload: () => void }) {
  const [manualSeverity, setManualSeverity] = useState("");
  const [manualCategory, setManualCategory] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api(`/api/incidents/${incident.id}/override`, {
        method: "PUT",
        body: JSON.stringify({
          manual_severity: manualSeverity || undefined,
          manual_category: manualCategory || undefined,
          override_reason: overrideReason,
        }),
      });
      onReload();
      onUpdate();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Override failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1 block text-xs text-slate-400">Override Severity (Optional)</label>
        <select
          value={manualSeverity}
          onChange={(e) => setManualSeverity(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
        >
          <option value="">Keep Original</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block text-xs text-slate-400">Override Category (Optional)</label>
        <select
          value={manualCategory}
          onChange={(e) => setManualCategory(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
        >
          <option value="">Keep Original</option>
          <option value="murder">Murder</option>
          <option value="assault">Assault</option>
          <option value="robbery">Robbery</option>
          <option value="rape">Rape</option>
          <option value="theft">Theft</option>
          <option value="burglary">Burglary</option>
          <option value="vandalism">Vandalism</option>
          <option value="drug_offence">Drug Offence</option>
          <option value="fraud">Fraud</option>
          <option value="suspicious_activity">Suspicious Activity</option>
          <option value="noise_complaint">Noise Complaint</option>
          <option value="domestic_dispute">Domestic Dispute</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block text-xs text-slate-400">Override Reason (Required)</label>
        <textarea
          value={overrideReason}
          onChange={(e) => setOverrideReason(e.target.value)}
          placeholder="Explain why this override is necessary..."
          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
          rows={3}
          required
        />
      </div>

      {error && (
        <div className="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !overrideReason}
        className="w-full rounded-lg bg-cyan-600 py-2 text-sm font-semibold hover:bg-cyan-500 disabled:opacity-50"
      >
        {loading ? "Applying Override..." : "Apply Override"}
      </button>
    </form>
  );
}

export default function IncidentsPage() {
  return <AppShell><IncidentsInner /></AppShell>;
}