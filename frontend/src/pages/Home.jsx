import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import SearchBar from "../components/SearchBar";
import VerdictCard from "../components/VerdictCard";
import EvidenceCard from "../components/EvidenceCard";
import ReasonCard from "../components/ReasonCard";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const HISTORY_KEY = "fakeye_history_v1";

/* ================= LOGIC ================= */

function mapBackendToVerdict(be) {
  if (!be) {
    return { verdict: "Unverifiable", confidence: 0, summary: "", reason: "" };
  }

  const rawLabel = be.verdict_raw_label || null;
  const percent =
    typeof be.verdict_percent === "number" ? be.verdict_percent : 0;

  let verdict = "Unverifiable";
  if (rawLabel === "True") verdict = "True";
  else if (rawLabel === "False") verdict = "False";

  const confidence = Math.round(Math.max(0, Math.min(100, percent)));

  const summary =
    be.verdict_summary ||
    (verdict === "True"
      ? "Multiple credible sources support this claim."
      : verdict === "False"
      ? "Credible sources contradict this claim."
      : "Available evidence is inconclusive.");

  const reason = be.verdict_reason || "";

  return { verdict, confidence, summary, reason };
}

function mapMatchesToEvidence(matches = []) {
  return matches.map((m) => {
    const url = m.url || null;
    let publisher = m.publisher || null;

    if (!publisher && url) {
      try {
        publisher = new URL(url).hostname.replace("www.", "");
      } catch {
        publisher = url;
      }
    }

    return {
      url,
      publisher,
      snippet: m.snippet || "",
      stance: m.stance || "neutral",
      stance_conf: Number(m.stance_conf || 0.5),
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
  const evidenceItems = mapMatchesToEvidence(resultRaw?.top_matches || []);

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
            across the web and explains why.
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
                  <div className="text-sm text-slate-400">
                    Searching the web…
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {error && (
              <div className="p-4 rounded-xl bg-rose-500/10 text-rose-300">
                {error}
              </div>
            )}

            {resultRaw && !loading && (
              <>
                <VerdictCard
                  verdict={mapped.verdict}
                  confidence={mapped.confidence}
                  summary={mapped.summary}
                />

                <ReasonCard reason={mapped.reason} />

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
                      <div className="text-slate-400">
                        No evidence found.
                      </div>
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
