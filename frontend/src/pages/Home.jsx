import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import SearchBar from "../components/SearchBar";
import VerdictCard from "../components/VerdictCard";
import EvidenceCard from "../components/EvidenceCard";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const HISTORY_KEY = "fakeye_history_v1";

/* ================= LOGIC (UNCHANGED) ================= */

function mapBackendToVerdict(be) {
  if (!be) return { verdict: "Unverifiable", confidence: 0, summary: "" };

  const rawLabel = be.verdict_raw_label || null;
  const machineLabel = be.verdict_machine_label || be.verdict || null;
  const percent = typeof be.verdict_percent === "number" ? be.verdict_percent : null;

  const legacy_verdict = be.verdict;
  const legacy_score = be.verdict_score || {};

  let mappedVerdict;
  if (rawLabel === "True" || (machineLabel && machineLabel.toLowerCase().includes("true"))) mappedVerdict = "True";
  else if (rawLabel === "False" || (machineLabel && machineLabel.toLowerCase().includes("false"))) mappedVerdict = "False";
  else if (rawLabel === "Mixture" || rawLabel === "Unverifiable") mappedVerdict = "Unverifiable";
  else mappedVerdict = legacy_verdict === "likely_real" ? "True" : legacy_verdict === "suspicious" ? "False" : "Unverifiable";

  let confidence = 0;
  if (percent !== null) confidence = Math.round(Math.max(0, Math.min(100, percent)));
  else if (legacy_score?.result_count || legacy_score?.credible_host_count) {
    const rc = legacy_score.result_count || 0;
    const cred = legacy_score.credible_host_count || 0;
    confidence = Math.min(100, Math.round((cred / Math.max(1, rc)) * 100));
  } else confidence = 30;

  const summary =
    be.verdict_summary ||
    be.summary ||
    (mappedVerdict === "True"
      ? "Multiple credible sources report similar information."
      : mappedVerdict === "False"
      ? "No matching credible sources found; the claim appears dubious."
      : "Some matches found but context is uncertain — inspect the links.");

  return { verdict: mappedVerdict, confidence, summary };
}

function mapMatchesToEvidence(matches = [], backendLabel) {
  return matches.map((m) => {
    const url = m.url || m.link || m.href || null;
    let publisher = m.publisher || m.title || null;

    if (!publisher && url) {
      try {
        publisher = new URL(url).hostname.replace("www.", "");
      } catch {
        publisher = url;
      }
    }

    const snippet = m.snippet || m.description || m.summary || "";

    let stance = (m.stance || "").toLowerCase();
    if (!stance) {
      if (backendLabel?.toLowerCase().includes("true")) stance = "support";
      else if (backendLabel?.toLowerCase().includes("false")) stance = "contradict";
      else stance = "neutral";
    }

    return {
      url,
      publisher,
      snippet,
      stance,
      stance_conf: Number(m.stance_conf || 0.6),
      semantic_sim: Number(m.semantic_sim || 0.5),
    };
  });
}

/* ================= COMPONENT ================= */

export default function Home() {
  const [query, setQuery] = useState("");
  const [resultRaw, setResultRaw] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) setHistory(JSON.parse(raw));
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 30)));
    } catch {}
  }, [history]);

  async function onSearch(q) {
    setQuery(q);
    setResultRaw(null);
    setError("");
    if (!q?.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: q }),
      });

      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const json = await res.json();

      setResultRaw(json);
      setHistory((h) => [{ q, raw: json, ts: Date.now() }, ...h].slice(0, 30));
    } catch (e) {
      setError(e.message || "Network error");
    } finally {
      setLoading(false);
    }
  }

  function clearHistory() {
    setHistory([]);
    localStorage.removeItem(HISTORY_KEY);
  }

  const mapped = mapBackendToVerdict(resultRaw);
  const evidenceItems = mapMatchesToEvidence(
    resultRaw?.top_matches || resultRaw?.matches || [],
    resultRaw?.verdict_raw_label || resultRaw?.verdict_machine_label
  );

  /* ================= UI ================= */

  return (
    <div
      className="min-h-screen text-white"
      style={{
        background:
          "radial-gradient(1200px 800px at 10% 10%, #0b1416, #071015 30%, #06070a 100%)",
      }}
    >
      <div className="max-w-6xl mx-auto px-6 py-10">
        <motion.header
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-2">
            Fakeye
          </h1>
          <p className="text-slate-300 max-w-2xl">
            Quick claim checking — finds supporting or contradicting reporting
            across the web and surfaces concise evidence.
          </p>
        </motion.header>

        <div className="mt-8">
          <SearchBar onSearch={onSearch} defaultValue={query} loading={loading} />
        </div>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <AnimatePresence>
              {loading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="p-6 neu rounded-2xl"
                >
                  <div className="text-sm text-slate-400">Searching the web…</div>
                </motion.div>
              )}
            </AnimatePresence>

            {resultRaw && !loading && (
              <>
                <VerdictCard
                  verdict={mapped.verdict}
                  confidence={mapped.confidence}
                  summary={mapped.summary}
                />

                <section>
                  <h3 className="text-sm text-slate-400 mb-3">
                    Top evidence
                  </h3>
                  <div className="space-y-3">
                    {evidenceItems.length ? (
                      evidenceItems.map((it, i) => (
                        <EvidenceCard key={i} item={it} />
                      ))
                    ) : (
                      <div className="text-slate-400">No evidence found.</div>
                    )}
                  </div>
                </section>
              </>
            )}
          </div>

          <aside className="space-y-4">
            <div className="neu p-4 rounded-2xl">
              <div className="flex justify-between text-sm">
                <span>History</span>
                <button onClick={clearHistory} className="text-slate-400">
                  Clear
                </button>
              </div>

              <div className="mt-3 space-y-2 max-h-64 overflow-auto">
                {history.length === 0 && (
                  <div className="text-xs text-slate-400">
                    No recent checks yet.
                  </div>
                )}
                {history.map((h, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setQuery(h.q);
                      setResultRaw(h.raw);
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className="w-full text-left p-3 rounded-md neu"
                  >
                    <div className="text-sm truncate">{h.q}</div>
                    <div className="text-xs text-slate-400">
                      {new Date(h.ts).toLocaleString()}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </aside>
        </div>

        <footer className="mt-10 text-center text-xs text-slate-500">
          Built with ❤️ — Fakeye
        </footer>
      </div>
    </div>
  );
}


// // src/pages/Home.jsx
// import React, { useEffect, useState } from "react";
// import { motion, AnimatePresence } from "framer-motion";
// import SearchBar from "../components/SearchBar";
// import VerdictCard from "../components/VerdictCard";
// import EvidenceCard from "../components/EvidenceCard";

// const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
// const HISTORY_KEY = "fakeye_history_v1";

// /**
//  * mapBackendToVerdict: robust mapping for both old & new backend responses.
//  * - new backend: verdict_raw_label, verdict_label, verdict_machine_label, verdict_percent
//  * - legacy backend: verdict (likely_real|suspicious|...), verdict_score { result_count, credible_host_count }
//  */
// function mapBackendToVerdict(be) {
//   if (!be) return { verdict: "Unverifiable", confidence: 0, summary: "" };

//   // Prefer new fields
//   const rawLabel = be.verdict_raw_label || null; // "True"/"False"/"Mixture"/"Unverifiable"
//   const humanLabel = be.verdict_label || null;
//   const machineLabel = be.verdict_machine_label || be.verdict || null;
//   const percent = typeof be.verdict_percent === "number" ? be.verdict_percent : null;

//   // legacy
//   const legacy_verdict = be.verdict;
//   const legacy_score = be.verdict_score || {};

//   // Determine mapped verdict
//   let mappedVerdict;
//   if (rawLabel === "True" || (machineLabel && machineLabel.toString().toLowerCase().includes("true"))) mappedVerdict = "True";
//   else if (rawLabel === "False" || (machineLabel && machineLabel.toString().toLowerCase().includes("false"))) mappedVerdict = "False";
//   else if (rawLabel === "Mixture") mappedVerdict = "Unverifiable";
//   else if (rawLabel === "Unverifiable") mappedVerdict = "Unverifiable";
//   else {
//     mappedVerdict = legacy_verdict === "likely_real" ? "True" : legacy_verdict === "suspicious" ? "False" : "Unverifiable";
//   }

//   // Confidence: prefer percent, else legacy heuristic, else infer from machineLabel
//   let confidence = 0;
//   if (percent !== null) {
//     confidence = Math.round(Math.max(0, Math.min(100, percent)));
//   } else if (legacy_score && (legacy_score.result_count || legacy_score.credible_host_count)) {
//     const rc = legacy_score.result_count || 0;
//     const cred = legacy_score.credible_host_count || 0;
//     confidence = Math.min(100, Math.round((cred / Math.max(1, rc)) * 100));
//   } else {
//     if (machineLabel && machineLabel.toString().toLowerCase().includes("definitely")) confidence = 90;
//     else if (machineLabel && machineLabel.toString().toLowerCase().includes("likely")) confidence = 75;
//     else if (machineLabel && machineLabel.toString().toLowerCase().includes("possibly")) confidence = 55;
//     else confidence = 30;
//   }

//   // Summary: prefer returned summary
//   const summary = be.verdict_summary || be.summary || (
//     mappedVerdict === "True"
//       ? "Multiple credible sources report similar information."
//       : mappedVerdict === "False"
//       ? "No matching credible sources found; the claim appears dubious."
//       : "Some matches found but context is uncertain — inspect the links."
//   );

//   return { verdict: mappedVerdict, confidence, summary };
// }

// /**
//  * mapMatchesToEvidence: canonicalize match objects to the shape EvidenceCard expects.
//  * Accepts both new 'top_matches' items and older shapes.
//  */
// function mapMatchesToEvidence(matches = [], backendLabelOrMachineLabel) {
//   return matches.map((m) => {
//     const url = m.url || m.link || m.href || null;

//     let publisher = m.publisher || m.title || null;
//     if (!publisher && url) {
//       try {
//         publisher = new URL(url).hostname.replace("www.", "");
//       } catch (e) {
//         publisher = url;
//       }
//     }

//     const snippet = m.snippet || m.description || m.summary || "";

//     let stance = (m.stance || "").toLowerCase();
//     if (!stance) {
//       if (backendLabelOrMachineLabel) {
//         const bl = backendLabelOrMachineLabel.toString().toLowerCase();
//         if (bl.includes("true") || bl.includes("real") || bl.includes("support")) stance = "support";
//         else if (bl.includes("false") || bl.includes("suspicious") || bl.includes("contradict")) stance = "contradict";
//         else stance = "neutral";
//       } else {
//         stance = "neutral";
//       }
//     }

//     const stance_conf = typeof m.stance_conf === "number" ? m.stance_conf : (m.score || m.semantic_sim || (stance === "support" ? 0.7 : stance === "contradict" ? 0.65 : 0.45));
//     const semantic_sim = typeof m.semantic_sim === "number" ? m.semantic_sim : (m.score || Math.min(0.95, Math.max(0.12, (snippet.length || 40) / 220)));

//     return {
//       url,
//       publisher,
//       snippet,
//       stance,
//       stance_conf: Number(stance_conf),
//       semantic_sim: Number(semantic_sim),
//     };
//   });
// }

// export default function Home() {
//   const [query, setQuery] = useState("");
//   const [resultRaw, setResultRaw] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState("");
//   const [history, setHistory] = useState([]);

//   useEffect(() => {
//     try {
//       const raw = localStorage.getItem(HISTORY_KEY);
//       if (raw) setHistory(JSON.parse(raw));
//     } catch (e) {}
//   }, []);

//   useEffect(() => {
//     try {
//       localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 30)));
//     } catch (e) {}
//   }, [history]);

//   async function onSearch(q) {
//     setQuery(q);
//     setResultRaw(null);
//     setError("");
//     if (!q || !q.trim()) return;
//     setLoading(true);

//     try {
//       const res = await fetch(`${API}/predict`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ text: q }),
//       });

//       if (!res.ok) {
//         const json = await res.json().catch(() => ({}));
//         throw new Error(json.detail || `Server returned ${res.status}`);
//       }

//       const json = await res.json();
//       // debug log for developer tools
//       console.debug("API /predict response:", json);
//       setResultRaw(json);

//       setHistory((h) => [{ q, raw: json, ts: Date.now() }, ...h.filter((x) => x.q !== q)].slice(0, 30));
//     } catch (e) {
//       console.error(e);
//       setError(e?.message || "Network error");
//     } finally {
//       setLoading(false);
//     }
//   }

//   function clearHistory() {
//     setHistory([]);
//     localStorage.removeItem(HISTORY_KEY);
//   }

//   const mapped = mapBackendToVerdict(resultRaw);
//   const evidenceItems = mapMatchesToEvidence(resultRaw?.top_matches || resultRaw?.topMatches || resultRaw?.matches || [], resultRaw?.verdict_raw_label || resultRaw?.verdict_machine_label || resultRaw?.verdict);

//   const hasResult = !!resultRaw;

//   return (
//     <div className="min-h-screen" style={{ background: "radial-gradient(1200px 800px at 10% 10%, #0b1416, #071015 30%, #06070a 100%)", color: "var(--tw-text-opacity, 1)" }}>
//       <div className="max-w-6xl mx-auto px-6 py-10">
//         <motion.header initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.35 }}>
//           <div className="flex items-start gap-6">
//             <motion.div
//               layout
//               animate={hasResult ? { scale: 0.9, x: 0, y: 0 } : { scale: 1 }}
//               transition={{ type: "spring", stiffness: 300, damping: 24 }}
//               className="flex-1"
//             >
//               <h1 className={`text-4xl md:text-5xl font-extrabold tracking-tight`} style={{ color: "#F8FAFB", marginBottom: 8 }}>
//                 Fakeye
//               </h1>
//               <p className="text-slate-300 max-w-2xl">
//                 Quick claim checking — finds supporting or contradicting reporting across the web and surfaces concise evidence.
//                 Fast, visual, and privacy-friendly.
//               </p>
//             </motion.div>

//             <div className="hidden md:flex items-center">
//               <div className="text-xs text-slate-400 mr-4">Recent</div>
//               <div className="flex gap-2">
//                 <button onClick={() => { if (history[0]) onSearch(history[0].q); }} className="px-3 py-2 rounded-md neu text-sm">Check latest</button>
//                 <button onClick={clearHistory} className="px-3 py-2 rounded-md neu text-sm">Clear</button>
//               </div>
//             </div>
//           </div>
//         </motion.header>

//         <motion.div layout className="mt-8">
//           <SearchBar onSearch={onSearch} defaultValue={query} loading={loading} />
//         </motion.div>

//         <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
//           <div className="lg:col-span-2 space-y-6">
//             <AnimatePresence>
//               {loading && (
//                 <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-6 neu rounded-2xl">
//                   <div className="text-sm text-slate-400 mb-2">Searching the web...</div>
//                   <div className="h-4 bg-slate-800 rounded w-3/5 animate-pulse" />
//                   <div className="mt-3 h-3 bg-slate-800 rounded w-2/3 animate-pulse" />
//                 </motion.div>
//               )}
//             </AnimatePresence>

//             <AnimatePresence>
//               {resultRaw && !loading && (
//                 <motion.div key="result" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}>
//                   <VerdictCard verdict={mapped.verdict} confidence={mapped.confidence} summary={mapped.summary} />
//                 </motion.div>
//               )}
//             </AnimatePresence>

//             {resultRaw && !loading && (
//               <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
//                 {/* Top evidence (summary card removed per request) */}
//                 <div>
//                   <h3 className="text-sm text-slate-400 mb-3">Top evidence</h3>
//                   <div className="space-y-3">
//                     {evidenceItems.length ? evidenceItems.map((it, i) => <EvidenceCard key={i} item={it} />) : <div className="text-slate-400">No evidence found.</div>}
//                   </div>
//                 </div>
//               </motion.section>
//             )}
//           </div>

//           <aside className="space-y-4">
//             <div className="neu p-4 rounded-2xl">
//               <div className="flex items-center justify-between">
//                 <div className="text-sm font-medium text-slate-200">History</div>
//                 <div className="text-xs text-slate-400">{history.length} items</div>
//               </div>

//               <div className="mt-3 space-y-2 max-h-64 overflow-auto">
//                 {history.length === 0 && <div className="text-xs text-slate-400">No recent checks yet — try one above.</div>}
//                 {history.map((h, idx) => (
//                   <button
//                     key={idx}
//                     onClick={() => { setQuery(h.q); setResultRaw(h.raw); window.scrollTo({ top: 0, behavior: "smooth" }); }}
//                     className="w-full text-left p-3 rounded-md neu flex items-start gap-3 hover:translate-x-1 transition"
//                   >
//                     <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-xs text-slate-300 font-semibold">{(h.q || "").slice(0,2).toUpperCase()}</div>
//                     <div className="flex-1">
//                       <div className="text-sm text-slate-200 truncate">{h.q}</div>
//                       <div className="text-xs text-slate-400 mt-1">{new Date(h.ts).toLocaleString()}</div>
//                     </div>
//                   </button>
//                 ))}
//               </div>
//             </div>

//             <div className="neu p-4 rounded-2xl text-xs text-slate-400">
//               <div className="font-medium text-slate-200 mb-2">How it works</div>
//               <p className="text-xs">We search the live web, score matching sources and show supporting/contradicting evidence. Always open links to verify context.</p>
//             </div>
//           </aside>
//         </div>

//         <footer className="mt-10 text-center text-xs text-slate-500">
//           Built with ❤️ — Fakeye
//         </footer>
//       </div>
//     </div>
//   );
// }
