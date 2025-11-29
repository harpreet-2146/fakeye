// src/pages/Home.jsx
import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import SearchBar from "../components/SearchBar";
import VerdictCard from "../components/VerdictCard";
import EvidenceCard from "../components/EvidenceCard";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const HISTORY_KEY = "fakeye_history_v1";

/**
 * Helpers to adapt backend -> UI shape
 * backend returns { verdict: "likely_real"|"uncertain"|"suspicious", verdict_score: {...}, top_matches: [{title,link,snippet}] }
 * VerdictCard expects verdict="True"/"False"/"Unverifiable", confidence=number (0-100), summary=string
 * EvidenceCard expects item fields: url, publisher, snippet, stance, stance_conf, semantic_sim
 */

function mapBackendToVerdict(be) {
  if (!be) return { verdict: "Unverifiable", confidence: 0, summary: "" };
  const { verdict, verdict_score = {} } = be;
  // confidence heuristic: credible_host_count / max(1, result_count) scaled
  const rc = verdict_score.result_count || 0;
  const cred = verdict_score.credible_host_count || 0;
  const confidence = Math.min(100, Math.round((cred / Math.max(1, rc)) * 100));
  const summary =
    verdict === "likely_real"
      ? "Multiple credible sources report similar information."
      : verdict === "suspicious"
      ? "No matching credible sources found; the claim appears dubious."
      : "Some matches found but context is uncertain — inspect the links.";

  const mappedVerdict =
    verdict === "likely_real" ? "True" : verdict === "suspicious" ? "False" : "Unverifiable";

  return { verdict: mappedVerdict, confidence, summary };
}

function mapMatchesToEvidence(matches = [], verdictLabel) {
  // Create items shaped for EvidenceCard. We derive 'stance' from global verdict.
  return matches.map((m) => {
    const stance =
      verdictLabel === "likely_real" ? "support" : verdictLabel === "suspicious" ? "contradict" : "neutral";
    // stance_conf and semantic_sim are heuristics: try to use snippet length or leave defaults
    const stance_conf = stance === "support" ? 0.85 : stance === "contradict" ? 0.78 : 0.45;
    const semantic_sim = Math.min(0.99, Math.max(0.12, (m.snippet?.length || 40) / 200));
    return {
      url: m.link || m.url,
      publisher: m.title || (m.link ? new URL(m.link).hostname : undefined),
      snippet: m.snippet || m.description || "",
      stance,
      stance_conf,
      semantic_sim,
    };
  });
}

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
    } catch (e) {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 30)));
    } catch (e) {}
  }, [history]);

  async function onSearch(q) {
    setQuery(q);
    setResultRaw(null);
    setError("");
    if (!q || !q.trim()) return;
    setLoading(true);

    try {
      const res = await fetch(`${API}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: q }),
      });

      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        throw new Error(json.detail || `Server returned ${res.status}`);
      }

      const json = await res.json();
      // store raw for UI mapping
      setResultRaw(json);

      // save to history (most recent first)
      setHistory((h) => [{ q, raw: json, ts: Date.now() }, ...h.filter((x) => x.q !== q)].slice(0, 30));
    } catch (e) {
      console.error(e);
      setError(e?.message || "Network error");
    } finally {
      setLoading(false);
    }
  }

  function clearHistory() {
    setHistory([]);
    localStorage.removeItem(HISTORY_KEY);
  }

  const mapped = mapBackendToVerdict(resultRaw);
  const evidenceItems = mapMatchesToEvidence(resultRaw?.top_matches || [], resultRaw?.verdict);

  // Animation states: headline shrinks when result present
  const hasResult = !!resultRaw;

  return (
    <div className="min-h-screen" style={{ background: "radial-gradient(1200px 800px at 10% 10%, #0b1416, #071015 30%, #06070a 100%)", color: "var(--tw-text-opacity, 1)" }}>
      <div className="max-w-6xl mx-auto px-6 py-10">
        <motion.header initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.35 }}>
          <div className="flex items-start gap-6">
            <motion.div
              layout
              animate={hasResult ? { scale: 0.9, x: 0, y: 0 } : { scale: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 24 }}
              className="flex-1"
            >
              <h1 className={`text-4xl md:text-5xl font-extrabold tracking-tight`} style={{ color: "#F8FAFB", marginBottom: 8 }}>
                Fakeye
              </h1>
              <p className="text-slate-300 max-w-2xl">
                Quick claim checking — finds supporting or contradicting reporting across the web and surfaces concise evidence.
                Fast, visual, and privacy-friendly.
              </p>
            </motion.div>

            <div className="hidden md:flex items-center">
              <div className="text-xs text-slate-400 mr-4">Recent</div>
              <div className="flex gap-2">
                <button onClick={() => { if (history[0]) onSearch(history[0].q); }} className="px-3 py-2 rounded-md neu text-sm">Check latest</button>
                <button onClick={clearHistory} className="px-3 py-2 rounded-md neu text-sm">Clear</button>
              </div>
            </div>
          </div>
        </motion.header>

        {/* Search */}
        <motion.div layout className="mt-8">
          <SearchBar onSearch={onSearch} defaultValue={query} loading={loading} />
        </motion.div>

        {/* Content area */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: results */}
          <div className="lg:col-span-2 space-y-6">
            <AnimatePresence>
              {loading && (
                <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-6 neu rounded-2xl">
                  <div className="text-sm text-slate-400 mb-2">Searching the web...</div>
                  <div className="h-4 bg-slate-800 rounded w-3/5 animate-pulse" />
                  <div className="mt-3 h-3 bg-slate-800 rounded w-2/3 animate-pulse" />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Verdict area */}
            <AnimatePresence>
              {resultRaw && !loading && (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                >
                  <VerdictCard verdict={mapped.verdict} confidence={mapped.confidence} summary={mapped.summary} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Explanation / evidence */}
            {resultRaw && !loading && (
              <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                <div className="neu p-4 rounded-2xl">
                  <h3 className="text-sm text-slate-400 mb-3">Summary</h3>
                  <p className="text-sm text-slate-200">{mapped.summary}</p>
                </div>

                <div>
                  <h3 className="text-sm text-slate-400 mb-3">Top evidence</h3>
                  <div className="space-y-3">
                    {evidenceItems.length ? evidenceItems.map((it, i) => <EvidenceCard key={i} item={it} />) : <div className="text-slate-400">No evidence found.</div>}
                  </div>
                </div>
              </motion.section>
            )}
          </div>

          {/* Right: history + quick info */}
          <aside className="space-y-4">
            <div className="neu p-4 rounded-2xl">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-slate-200">History</div>
                <div className="text-xs text-slate-400">{history.length} items</div>
              </div>

              <div className="mt-3 space-y-2 max-h-64 overflow-auto">
                {history.length === 0 && <div className="text-xs text-slate-400">No recent checks yet — try one above.</div>}
                {history.map((h, idx) => (
                  <button
                    key={idx}
                    onClick={() => { setQuery(h.q); setResultRaw(h.raw); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                    className="w-full text-left p-3 rounded-md neu flex items-start gap-3 hover:translate-x-1 transition"
                  >
                    <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-xs text-slate-300 font-semibold">{(h.q || "").slice(0,2).toUpperCase()}</div>
                    <div className="flex-1">
                      <div className="text-sm text-slate-200 truncate">{h.q}</div>
                      <div className="text-xs text-slate-400 mt-1">{new Date(h.ts).toLocaleString()}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="neu p-4 rounded-2xl text-xs text-slate-400">
              <div className="font-medium text-slate-200 mb-2">How it works</div>
              <p className="text-xs">We search the live web, score matching sources and show supporting/contradicting evidence. Always open links to verify context.</p>
            </div>
          </aside>
        </div>

        {/* Footer */}
        <footer className="mt-10 text-center text-xs text-slate-500">
          Built with ❤️ — Fakeye
        </footer>
      </div>
    </div>
  );
}
