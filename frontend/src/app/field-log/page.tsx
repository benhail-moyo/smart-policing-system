"use client";

import { useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/client";
import { ClipboardPenLine, Send, CheckCircle2 } from "lucide-react";

function FieldLogInner() {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today); const [shift, setShift] = useState("Day shift");
  const [areaName, setAreaName] = useState(""); const [summary, setSummary] = useState("");
  const [message, setMessage] = useState<string | null>(null); const [error, setError] = useState<string | null>(null);
  async function submit(e: React.FormEvent) { e.preventDefault(); setError(null); try { await api("/api/command/logs", {method:"POST", body:JSON.stringify({date, shift, areaName, summary})}); setAreaName(""); setSummary(""); setMessage("Daily field log submitted for command review."); } catch (e) { setError(e instanceof Error ? e.message : "Could not submit log"); } }
  return <div className="mx-auto max-w-2xl p-5 md:p-8"><div className="mb-6"><h1 className="flex items-center gap-2 text-2xl font-bold"><ClipboardPenLine className="h-6 w-6 text-violet-400"/>Daily Field Log</h1><p className="mt-1 text-sm text-slate-400">Record your shift activity for the command team.</p></div>{message && <div className="mb-4 flex items-center gap-2 rounded-lg bg-emerald-500/15 px-4 py-3 text-sm text-emerald-200"><CheckCircle2 className="h-4 w-4"/>{message}</div>}{error && <div className="mb-4 rounded-lg bg-red-500/15 px-4 py-3 text-sm text-red-200">{error}</div>}<form onSubmit={submit} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm text-slate-300">Date<input type="date" value={date} onChange={e=>setDate(e.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5"/></label><label className="text-sm text-slate-300">Shift<select value={shift} onChange={e=>setShift(e.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5"><option>Day shift</option><option>Night shift</option><option>Overtime</option></select></label></div><label className="block text-sm text-slate-300">Patrol area<input required value={areaName} onChange={e=>setAreaName(e.target.value)} placeholder="e.g. CBD Sector 2" className="mt-1.5 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5"/></label><label className="block text-sm text-slate-300">Activity summary<textarea required rows={6} value={summary} onChange={e=>setSummary(e.target.value)} placeholder="Patrols completed, incidents attended, observations and handover notes…" className="mt-1.5 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5"/></label><button className="flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 py-2.5 text-sm font-bold hover:bg-violet-500"><Send className="h-4 w-4"/>Submit field log</button></form></div>;
}
export default function FieldLogPage() { return <AppShell><FieldLogInner /></AppShell>; }
