import React from "react";

export default function VerdictCard({ verdict="Unverifiable", confidence=0, summary="" }){
  const colorClass = verdict === "True" ? "text-emerald-300" : verdict === "False" ? "text-rose-300" : "text-amber-300";
  const bgClass = verdict === "True" ? "bg-emerald-500/6 border-emerald-400/10" : verdict === "False" ? "bg-rose-500/6 border-rose-400/10" : "bg-amber-500/6 border-amber-400/10";

  return (
    <div className={`p-5 rounded-2xl border ${bgClass} neu`}>
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-slate-400">Verdict</div>
          <div className="flex items-center gap-3">
            <div className={`text-2xl font-semibold ${colorClass}`}>{verdict}</div>
            <div className="text-sm text-slate-300">{confidence}%</div>
          </div>
        </div>
        <div className="text-xs text-slate-400">Checked just now</div>
      </div>

      <p className="mt-3 text-sm text-slate-200">{summary}</p>
    </div>
  );
}
