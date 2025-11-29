import React, { useState } from "react";
import SearchBar from "../components/SearchBar";
import VerdictCard from "../components/VerdictCard";
import EvidenceCard from "../components/EvidenceCard";
import { checkClaim } from "../services/claimApi";

export default function Home(){
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSearch(q){
    setQuery(q);
    setResult(null);
    setError("");
    if(!q || !q.trim()) return;
    setLoading(true);
    try {
      const res = await checkClaim(q);
      setResult(res);
    } catch (e){
      console.error(e);
      setError(e?.message || "Network error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen p-6 bg-[#0B0F12] text-slate-100">
      <div className="max-w-5xl mx-auto">
        <header className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-semibold">Fakeye — Claim Checker</h1>
            <p className="text-slate-400 text-sm">Type a claim, get a verdict, summary and evidence links.</p>
          </div>
        </header>

        <SearchBar onSearch={onSearch} defaultValue={query} loading={loading} />

        {error && <div className="mt-4 text-rose-400">{error}</div>}

        {loading && <div className="mt-6 text-slate-400">Checking — this may take a few seconds...</div>}

        {result && (
          <div className="mt-6 space-y-6">
            <VerdictCard verdict={result.verdict} confidence={result.confidence} summary={result.summary} />

            <section className="grid md:grid-cols-3 gap-6">
              <div className="md:col-span-2 space-y-4">
                <div className="neu p-4">
                  <h3 className="text-sm text-slate-400 mb-3">Top evidence</h3>
                  <div className="space-y-3">
                    {result.evidence && result.evidence.length ? (
                      result.evidence.map((ev, i) => <EvidenceCard key={i} item={ev} />)
                    ) : (
                      <div className="text-slate-400 text-sm">No evidence items found.</div>
                    )}
                  </div>
                </div>

                <div className="neu p-4">
                  <h3 className="text-sm text-slate-400 mb-3">Explanation</h3>
                  <p className="text-sm text-slate-200">{result.summary}</p>
                </div>
              </div>

              <aside className="space-y-4">
                <div className="neu p-4">
                  <h4 className="text-sm text-slate-400">Source notes</h4>
                  <p className="text-xs text-slate-300 mt-2">
                    Sources are automatically retrieved and scored. Always open links to confirm context.
                  </p>
                </div>
                <div className="neu p-4 text-sm">
                  <div className="text-slate-300">Controls</div>
                  <div className="mt-3 flex gap-2">
                    <button className="px-3 py-2 rounded-lg">Re-check</button>
                    <button className="px-3 py-2 rounded-lg">View raw</button>
                  </div>
                </div>
              </aside>
            </section>
          </div>
        )}

        <footer className="mt-10 text-center text-xs text-slate-500">
          Built with ❤️ — results provided by Fakeye pipeline.
        </footer>
      </div>
    </div>
  );
}
