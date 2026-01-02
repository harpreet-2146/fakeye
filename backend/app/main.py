import os
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from app.retriever.rank import rank_snippets
from app.retriever.aggregate import aggregate_verdict
from app.retriever.stance import detect_stance

app = FastAPI(title="fakeye-api")

logger = logging.getLogger("uvicorn.error")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    text: str


def serp_search(query: str, api_key: str, num: int = 10) -> dict:
    url = "https://serpapi.com/search.json"
    params = {"q": query, "api_key": api_key, "num": num}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@app.get("/")
async def root():
    return {"ok": True, "status": "Fakeye API (Groq stance)"}


@app.post("/predict")
async def predict(req: PredictRequest):
    if not SERPAPI_API_KEY:
        raise HTTPException(500, "SERPAPI_API_KEY not set")

    claim = (req.text or "").strip()
    if not claim:
        raise HTTPException(400, "Empty text")

    try:
        json_resp = serp_search(claim, SERPAPI_API_KEY, num=10)
    except Exception:
        logger.exception("Search failed")
        raise HTTPException(502, "Search failed")

    organic = json_resp.get("organic_results") or []
    candidates = []

    for hit in organic:
        title = hit.get("title") or ""
        snippet = hit.get("snippet") or ""
        url = hit.get("link")
        candidates.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "text": f"{title} {snippet}".strip()
        })

    ranked = await rank_snippets(claim, candidates, top_k=min(10, len(candidates)))

    evidence = []

    for r in ranked:
        snippet_text = r.get("snippet") or r.get("text") or ""

        llm_result = detect_stance(claim, snippet_text)

        publisher = None
        if r.get("url"):
            try:
                publisher = r.get("url").split("/")[2]
            except Exception:
                pass

        evidence.append({
            "url": r.get("url"),
            "publisher": publisher,
            "text": r.get("text"),
            "snippet": snippet_text,
            "semantic_sim": float(r.get("score", 0.0)),
            "stance": llm_result.stance,
            "stance_conf": float(llm_result.confidence),
            "explanation": llm_result.explanation,
        })

    # ✅ AGGREGATE VERDICT
    raw_label, percent, summary, _ = aggregate_verdict(
        claim, evidence, verbose=False
    )

    # ✅ PICK STRONGEST REASON
    verdict_reason = None
    best_conf = -1.0

    for e in evidence:
        if e["stance"] in ("support", "contradict") and e["stance_conf"] > best_conf:
            verdict_reason = e["explanation"]
            best_conf = e["stance_conf"]

    if not verdict_reason:
        verdict_reason = summary

    return {
        "ok": True,
        "input": claim,
        "verdict_percent": round(percent, 2),
        "verdict_raw_label": raw_label,
        "verdict_summary": summary,
        "verdict_reason": verdict_reason,   # ✅ THIS MAKES REASON CARD APPEAR
        "top_matches": evidence[:5],
    }
