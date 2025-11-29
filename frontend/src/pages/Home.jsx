import { useState } from "react";
import { checkClaim } from "../services/claimApi";

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    const res = await checkClaim(query);
    setResult(res);
    setLoading(false);
  }

  return (
    <div className="p-8 text-slate-200 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Fakeye — Claim Checker</h1>

      <div className="flex gap-3 mb-6">
        <input
          className="neu-inset p-4 flex-1 outline-none"
          placeholder="Type a claim..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          className="neu px-6 py-3"
          onClick={handleSearch}
        >
          Check
        </button>
      </div>

      {loading && <div className="text-slate-400">Checking...</div>}

      {result && (
        <pre className="text-sm whitespace-pre-wrap mt-6 neu p-6">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
