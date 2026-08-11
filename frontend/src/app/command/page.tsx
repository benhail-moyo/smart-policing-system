"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import AppShell from "@/components/AppShell";
import { api, getStoredUser } from "@/lib/client";
import type { MapDeployment } from "@/components/CrimeMap";
import { Radio, Footprints, Car, ClipboardList, MapPin, Plus, ShieldAlert, UsersRound, CalendarDays, LockKeyhole } from "lucide-react";

const CrimeMap = dynamic(() => import("@/components/CrimeMap"), { ssr: false, loading: () => <div className="flex h-full items-center justify-center text-slate-400">Loading operational map…</div> });

type Plan = { id: number; title: string; type: string; areaName: string; scheduledFor?: string; personnel: number; notes: string; status: string };
type Log = { id: number; officer: string; date: string; shift: string; areaName: string; summary: string; status: string };

function CommandInner() {
  const [deployments, setDeployments] = useState<MapDeployment[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [logs, setLogs] = useState<Log[]>([]);
  const [point, setPoint] = useState<{lat:number;lng:number} | null>(null);
  const [unitType, setUnitType] = useState<"foot" | "vehicle">("foot");
  const [areaName, setAreaName] = useState("");
  const [instructions, setInstructions] = useState("");
  const [planTitle, setPlanTitle] = useState("");
  const [planType, setPlanType] = useState("Roadblock");
  const [planArea, setPlanArea] = useState("");
  const [personnel, setPersonnel] = useState(6);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const user = getStoredUser();

  async function load() {
    const [d, p, l] = await Promise.all([
      api<{deployments: MapDeployment[]}>("/api/command/deployments"),
      api<{plans: Plan[]}>("/api/command/plans"),
      api<{logs: Log[]}>("/api/command/logs"),
    ]);
    setDeployments(d.deployments); setPlans(p.plans); setLogs(l.logs);
  }
  useEffect(() => { if (user?.role === "admin") load().catch(e => setError(e.message)); }, [user?.role]);

  async function dispatch(e: React.FormEvent) {
    e.preventDefault(); setError(null);
    if (!point || !areaName.trim()) return setError("Choose a location on the map and name the deployment area.");
    try {
      const r = await api<{deployment: MapDeployment}>("/api/command/deployments", {method:"POST", body:JSON.stringify({unitType, areaName, instructions, ...point})});
      setDeployments(x => [r.deployment, ...x]); setPoint(null); setAreaName(""); setInstructions(""); setNotice(`${unitType === "foot" ? "Foot personnel" : "Vehicle unit"} deployment marked.`);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to mark deployment"); }
  }
  async function addPlan(e: React.FormEvent) {
    e.preventDefault(); setError(null);
    if (!planTitle.trim() || !planArea.trim()) return setError("Give the plan a name and operational area.");
    try {
      const r = await api<{plan: Plan}>("/api/command/plans", {method:"POST", body:JSON.stringify({title:planTitle, type:planType, areaName:planArea, personnel, status:"scheduled"})});
      setPlans(x => [r.plan, ...x]); setPlanTitle(""); setPlanArea(""); setNotice("Strategic operation scheduled.");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to create plan"); }
  }
  if (user?.role !== "admin") return <div className="p-8"><div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-red-200"><LockKeyhole className="mb-2 h-6 w-6"/>The Command Centre is restricted to administrators.</div></div>;

  return <div className="min-h-full bg-slate-950 p-4 md:p-7">
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4"><div><div className="mb-2 flex items-center gap-2 text-cyan-300"><Radio className="h-5 w-5"/><span className="text-xs font-bold uppercase tracking-[0.24em]">Secure command environment</span></div><h1 className="text-3xl font-bold">Operations Command Centre</h1><p className="mt-1 text-sm text-slate-400">Coordinate deployments, strategic operations and field accountability.</p></div><div className="rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-right"><div className="text-xs text-cyan-200">ACTIVE DEPLOYMENTS</div><div className="text-2xl font-bold">{deployments.length}</div></div></div>
    {error && <div className="mb-4 rounded-lg bg-red-500/15 px-4 py-3 text-sm text-red-200">{error}</div>}{notice && <div className="mb-4 rounded-lg bg-emerald-500/15 px-4 py-3 text-sm text-emerald-200">{notice}</div>}
    <div className="grid gap-5 xl:grid-cols-[370px_minmax(0,1fr)]">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><h2 className="flex items-center gap-2 font-semibold"><MapPin className="h-4 w-4 text-cyan-400"/>Mark a deployment</h2><p className="mb-4 mt-1 text-xs text-slate-400">Click the map, then assign the appropriate response type.</p><form onSubmit={dispatch} className="space-y-3"><div className="grid grid-cols-2 gap-2">{(["foot","vehicle"] as const).map(type => <button type="button" key={type} onClick={()=>setUnitType(type)} className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-semibold ${unitType===type ? "border-cyan-400 bg-cyan-400/15 text-cyan-100" : "border-slate-700 bg-slate-800 text-slate-300"}`}>{type === "foot" ? <Footprints className="h-4 w-4"/> : <Car className="h-4 w-4"/>}{type === "foot" ? "Foot" : "Vehicle"}</button>)}</div><input value={areaName} onChange={e=>setAreaName(e.target.value)} placeholder="Area / landmark" className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm"/><textarea value={instructions} onChange={e=>setInstructions(e.target.value)} placeholder="Brief instructions (optional)" rows={3} className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm"/><div className="rounded-lg bg-slate-950 px-3 py-2 text-xs text-slate-400">{point ? `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}` : "Awaiting map location"}</div><button className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-500 py-2.5 text-sm font-bold text-slate-950 hover:bg-cyan-400"><Plus className="h-4 w-4"/>Mark deployment</button></form><div className="mt-5 space-y-2 border-t border-slate-800 pt-4">{deployments.slice(0,4).map(d=><div key={d.id} className="flex items-center gap-3 rounded-lg bg-slate-800/70 p-3 text-xs"><span className={`flex h-7 w-7 items-center justify-center rounded-full ${d.unitType === "foot" ? "bg-emerald-400/15 text-emerald-300" : "bg-sky-400/15 text-sky-300"}`}>{d.unitType === "foot" ? <Footprints className="h-4 w-4"/>:<Car className="h-4 w-4"/>}</span><div><b className="block text-slate-200">{d.areaName}</b><span className="text-slate-400">{d.unitType} personnel · active</span></div></div>)}</div></section>
      <section className="min-h-[480px] overflow-hidden rounded-2xl border border-slate-800"><CrimeMap deployments={deployments} selected={point} onMapClick={(lat,lng)=>setPoint({lat,lng})} showIncidents={false} height="560px"/></section>
    </div>
    <div className="mt-6 grid gap-5 xl:grid-cols-2"><section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><h2 className="flex items-center gap-2 font-semibold"><ShieldAlert className="h-4 w-4 text-orange-400"/>Strategic operations</h2><form onSubmit={addPlan} className="mt-4 grid gap-2 sm:grid-cols-2"><input value={planTitle} onChange={e=>setPlanTitle(e.target.value)} placeholder="Operation name" className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"/><select value={planType} onChange={e=>setPlanType(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"><option>Roadblock</option><option>High-visibility patrol</option><option>Targeted operation</option><option>Community engagement</option></select><input value={planArea} onChange={e=>setPlanArea(e.target.value)} placeholder="Operational area" className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"/><input type="number" min="0" value={personnel} onChange={e=>setPersonnel(Number(e.target.value))} className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm"/><button className="sm:col-span-2 rounded-lg bg-orange-500 px-3 py-2 text-sm font-bold text-slate-950 hover:bg-orange-400">Schedule operation</button></form><div className="mt-4 space-y-2">{plans.slice(0,4).map(p=><div key={p.id} className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 p-3"><div><b className="text-sm">{p.title}</b><p className="text-xs text-slate-400">{p.type} · {p.areaName}</p></div><span className="rounded-full bg-orange-500/15 px-2 py-1 text-xs text-orange-300">{p.personnel} personnel</span></div>)}</div></section><section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><h2 className="flex items-center gap-2 font-semibold"><ClipboardList className="h-4 w-4 text-violet-400"/>Officer daily field logs</h2><p className="mt-1 text-xs text-slate-400">Submitted field activity and shift notes.</p><div className="mt-4 space-y-2">{logs.length ? logs.slice(0,5).map(log=><div key={log.id} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"><div className="flex justify-between gap-3"><b className="text-sm">{log.officer}</b><span className="text-xs text-slate-500">{log.date} · {log.shift}</span></div><p className="mt-1 text-xs text-slate-400">{log.areaName} — {log.summary}</p></div>) : <div className="rounded-lg border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500"><UsersRound className="mx-auto mb-2 h-5 w-5"/>No field logs have been submitted yet.</div>}</div></section></div>
  </div>;
}

export default function CommandPage() { return <AppShell><CommandInner /></AppShell>; }
