import React from "react";

export default function EvidenceCard({ item }){
  const stanceColor = item.stance === "support" ? "bg-emerald-500/10 text-emerald-300" : item.stance === "contradict" ? "bg-rose-500/10 text-rose-300" : "bg-slate-700/20 text-slate-300";

  return (
    <article className="p-4 rounded-xl bg-[#0C1113] shadow-neu-sm border border-slate-800 flex justify-between">
      <div className="flex-1">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-medium line-clamp-2">{item.publisher || (new URL(item.url)).hostname}</div>
            <div className="text-xs text-slate-400 mt-1">{/* optional date */}</div>
          </div>
          <div className={`text-xs px-2 py-1 rounded-full ${stanceColor}`}>{item.stance}</div>
        </div>

        <p className="mt-3 text-sm text-slate-300 line-clamp-3">{item.snippet}</p>
        <div className="mt-3 text-xs text-slate-500">Conf: {(item.stance_conf*100).toFixed(0)}% • Sim: {(item.semantic_sim*100).toFixed(0)}%</div>
      </div>

      <div className="ml-4 flex flex-col gap-2">
        <a className="text-xs px-3 py-2 rounded-lg bg-[#081314] shadow-neu-sm" href={item.url} target="_blank" rel="noreferrer">Open</a>
      </div>
    </article>
  );
}
