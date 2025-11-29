import React, { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function FakeChecker() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const verdictColor = (v) => {
    if (v === "likely_real") return "bg-green-600";
    if (v === "suspicious") return "bg-red-600";
    if (v === "uncertain") return "bg-yellow-500";
    return "bg-gray-600";
  };

  async function handleCheck() {
    setError(null);
    setResult(null);
    const trimmed = text.trim();
    if (!trimmed) return setError("Enter a news headline or URL");

    setLoading(true);
    try {
      const res = await fetch(`${API}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const json = await res.json();

      if (!res.ok) {
        setError(json.detail || "Server error");
      } else {
        setResult(json);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto p-6 bg-white shadow-lg rounded-lg mt-10">
      <h1 className="text-2xl font-bold mb-4">Fake News Checker</h1>

      <textarea
        className="w-full border rounded p-2 h-32"
        placeholder="Paste headline or URL here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="flex items-center gap-3 mt-3">
        <button
          onClick={handleCheck}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {loading ? "Checking..." : "Check"}
        </button>

        <button
          onClick={() => { setText(""); setError(null); setResult(null); }}
          className="px-3 py-2 border rounded"
        >
          Clear
        </button>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-600 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <h2 className="font-semibold mb-2">Verdict:</h2>
          <span
            className={
              "px-3 py-1 text-white rounded-full " +
              verdictColor(result.verdict)
            }
          >
            {result.verdict.replace("_", " ")}
          </span>

          <h3 className="font-semibold mt-4">Score:</h3>
          <pre className="text-xs bg-white p-2 rounded">
            {JSON.stringify(result.verdict_score, null, 2)}
          </pre>

          <h3 className="font-semibold mt-4">Top Matches:</h3>
          <ul className="space-y-2 mt-2">
            {result.top_matches.map((m, i) => (
              <li key={i} className="p-2 bg-white rounded shadow">
                <div className="font-medium">{m.title}</div>
                <a
                  className="text-blue-600 text-sm"
                  href={m.link}
                  target="_blank"
                  rel="noreferrer"
                >
                  {m.link}
                </a>
                <div className="text-sm text-gray-700">{m.snippet}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
