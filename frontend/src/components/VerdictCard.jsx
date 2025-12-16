// // src/components/VerdictCard.jsx
// import React from "react";

// export default function VerdictCard({ verdict = "Unverifiable", confidence = 0, summary = "" }) {
//   const colorClass = verdict === "True" ? "text-emerald-300" : verdict === "False" ? "text-rose-300" : "text-amber-300";
//   const bgClass = verdict === "True" ? "bg-emerald-500/6 border-emerald-400/10" : verdict === "False" ? "bg-rose-500/6 border-rose-400/10" : "bg-amber-500/6 border-amber-400/10";

//   return (
//     <div className={`p-5 rounded-2xl border ${bgClass} neu`}>
//       <div className="flex items-center justify-between">
//         <div>
//           <div className="text-xs text-slate-400">Verdict</div>
//           <div className="flex items-center gap-3">
//             <div className={`text-2xl font-semibold ${colorClass}`}>{verdict}</div>
//             <div className="text-sm text-slate-300">{confidence}%</div>
//           </div>
//         </div>
//         <div className="text-xs text-slate-400">Checked just now</div>
//       </div>

//       <p className="mt-3 text-sm text-slate-200">{summary}</p>
//     </div>
//   );
// }

// frontend/src/components/VerdictCard.jsx - UPDATED VERSION
import React from "react";

export default function VerdictCard({ verdict = "Unverifiable", confidence = 0, summary = "" }) {
  // Color schemes
  const getVerdictStyle = () => {
    if (verdict === "True") {
      return {
        text: "text-emerald-300",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
        icon: "✓"
      };
    } else if (verdict === "False") {
      return {
        text: "text-rose-300",
        bg: "bg-rose-500/10",
        border: "border-rose-500/20",
        icon: "✕"
      };
    } else {
      return {
        text: "text-amber-300",
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
        icon: "?"
      };
    }
  };

  const style = getVerdictStyle();

  // Get confidence level text
  const getConfidenceLevel = () => {
    if (confidence >= 80) return "High";
    if (confidence >= 60) return "Moderate";
    if (confidence >= 40) return "Low";
    return "Very Low";
  };

  return (
    <div className={`rounded-2xl border ${style.border} ${style.bg} overflow-hidden`}>
      {/* Header Section */}
      <div className="p-6 pb-4">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`text-4xl font-bold ${style.text}`}>
              {style.icon}
            </div>
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
                Verdict
              </div>
              <div className={`text-2xl font-bold ${style.text}`}>
                {verdict}
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
              Confidence
            </div>
            <div className={`text-2xl font-bold ${style.text}`}>
              {confidence}%
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {getConfidenceLevel()}
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="mt-4 pt-4 border-t border-slate-700/50">
          <p className="text-sm text-slate-300 leading-relaxed">
            {summary}
          </p>
        </div>
      </div>

      {/* Footer Timestamp */}
      <div className="px-6 py-3 bg-slate-900/30 border-t border-slate-800/50">
        <div className="text-xs text-slate-500">
          Checked just now
        </div>
      </div>
    </div>
  );
}