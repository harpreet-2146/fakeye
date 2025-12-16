# app/main.py - COMPLETE UPDATED VERSION
import os
import logging
from typing import List

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from app.retriever.rank import rank_snippets
from app.retriever.aggregate import aggregate_verdict
from app.retriever.stance import simple_stance_heuristic

app = FastAPI(title="fakeye-api-debug")

logger = logging.getLogger("uvicorn.error")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

origins = ["http://localhost", "http://localhost:3000", "http://127.0.0.1", "null"]
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class PredictRequest(BaseModel):
    text: str

def serp_search(query: str, api_key: str, num: int = 10) -> dict:
    url = "https://serpapi.com/search.json"
    params = {"q": query, "api_key": api_key, "num": num}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def map_percent_to_label(percent: float, raw_label: str) -> dict:
    p = float(percent)
    rl = (raw_label or "").lower()
    if rl in ("unverifiable", ""):
        return {"label": "Uncertain — needs review", "machine_label": "uncertain"}
    if rl == "mixture":
        if p < 40:
            return {"label": "Conflicting / Unclear", "machine_label": "mixture_low_confidence"}
        elif p < 60:
            return {"label": "Unclear / Mixed signals", "machine_label": "mixture"}
        else:
            return {"label": "Possibly True / Mixed signals", "machine_label": "mixture_high_confidence"}
    if rl == "true":
        if p >= 80:
            return {"label": "Very Likely True", "machine_label": "definitely_true"}
        elif p >= 60:
            return {"label": "Likely True", "machine_label": "likely_true"}
        else:
            return {"label": "Possibly True", "machine_label": "possibly_true"}
    if rl == "false":
        if p <= 20:
            return {"label": "Very Likely False", "machine_label": "definitely_false"}
        elif p <= 40:
            return {"label": "Likely False", "machine_label": "likely_false"}
        else:
            return {"label": "Possibly False", "machine_label": "possibly_false"}
    return {"label": "Uncertain", "machine_label": "uncertain"}

@app.get("/")
async def root():
    return {"status": "Fakeye API v3 (improved stance detection)", "ok": True}

@app.post("/predict")
async def predict(req: PredictRequest):
    if not SERPAPI_API_KEY:
        raise HTTPException(500, "SERPAPI_API_KEY not set")
    
    claim = (req.text or "").strip()
    if not claim:
        raise HTTPException(400, "Empty text")
    
    try:
        json_resp = serp_search(claim, SERPAPI_API_KEY, num=10)
    except Exception as e:
        logger.exception("Search failed: %s", e)
        raise HTTPException(502, f"Search failed: {e}")
    
    organic = json_resp.get("organic_results") or json_resp.get("news_results") or []
    candidates = []
    for hit in organic:
        title = hit.get("title") or ""
        snippet = hit.get("snippet") or hit.get("description") or ""
        url = hit.get("link") or hit.get("url")
        candidates.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "text": f"{title} {snippet}".strip()
        })
    
    try:
        ranked = await rank_snippets(claim, candidates, top_k=min(10, len(candidates)))
    except Exception as e:
        logger.exception("ranking failed: %s", e)
        ranked = []
        for c in candidates[:5]:
            ranked.append({**c, "score": 0.0, "raw_sim": 0.0})
    
    # === IMPROVED EVIDENCE PROCESSING ===
    evidence = []
    for r in ranked:
        sim = float(r.get("score", 0.0) or 0.0)
        raw_sim = float(r.get("raw_sim", sim) or sim)
        snippet_text = r.get("snippet") or r.get("text") or ""
        
        # Get stance using improved heuristic
        stance = simple_stance_heuristic(snippet_text, claim)
        
        # CRITICAL: Boost confidence for support/contradict stances
        if stance == "support":
            stance_conf = min(1.0, raw_sim + 0.3)
        elif stance == "contradict":
            stance_conf = min(1.0, raw_sim + 0.25)
        else:
            stance_conf = raw_sim * 0.7
        
        publisher = None
        if r.get("url"):
            try:
                publisher = r.get("url").split("/")[2]
            except Exception:
                publisher = None
        
        evidence.append({
            "url": r.get("url"),
            "publisher": publisher,
            "text": r.get("text"),
            "snippet": snippet_text,
            "semantic_sim": sim,
            "stance": stance,
            "stance_conf": float(stance_conf)
        })
    
    raw_label, percent, summary, _ = aggregate_verdict(claim, evidence, verbose=False)
    mapped = map_percent_to_label(percent, raw_label)
    
    top_matches = []
    for e in evidence[:5]:
        top_matches.append({
            "publisher": e.get("publisher"),
            "url": e.get("url"),
            "snippet": (e.get("snippet") or "")[:300],
            "semantic_sim": round(e.get("semantic_sim", 0.0), 4),
            "stance": e.get("stance"),
            "stance_conf": round(e.get("stance_conf", 0.0), 4)
        })
    
    return {
        "ok": True,
        "input": claim,
        "verdict_percent": round(percent, 2),
        "verdict_label": mapped["label"],
        "verdict_machine_label": mapped["machine_label"],
        "verdict_raw_label": raw_label,
        "verdict_summary": summary,
        "top_matches": top_matches,
        "verdict_debug": {"evidence_count": len(evidence)}
    }

@app.post("/predict_debug")
async def predict_debug(req: PredictRequest):
    if not SERPAPI_API_KEY:
        raise HTTPException(500, "SERPAPI_API_KEY not set")
    
    claim = (req.text or "").strip()
    if not claim:
        raise HTTPException(400, "Empty text")
    
    try:
        json_resp = serp_search(claim, SERPAPI_API_KEY, num=10)
    except Exception as e:
        logger.exception("Search failed: %s", e)
        raise HTTPException(502, f"Search failed: {e}")
    
    organic = json_resp.get("organic_results") or json_resp.get("news_results") or []
    candidates = []
    for hit in organic:
        title = hit.get("title") or ""
        snippet = hit.get("snippet") or hit.get("description") or ""
        url = hit.get("link") or hit.get("url")
        candidates.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "text": f"{title} {snippet}".strip()
        })
    
    try:
        ranked = await rank_snippets(claim, candidates, top_k=min(10, len(candidates)))
    except Exception as e:
        logger.exception("ranking failed: %s", e)
        ranked = []
        for c in candidates[:5]:
            ranked.append({**c, "score": 0.0, "raw_sim": 0.0})
    
    # === IMPROVED EVIDENCE PROCESSING ===
    evidence = []
    for r in ranked:
        sim = float(r.get("score", 0.0) or 0.0)
        raw_sim = float(r.get("raw_sim", sim) or sim)
        snippet_text = r.get("snippet") or r.get("text") or ""
        
        # Get stance using improved heuristic
        stance = simple_stance_heuristic(snippet_text, claim)
        
        # CRITICAL: Boost confidence for support/contradict stances
        if stance == "support":
            stance_conf = min(1.0, raw_sim + 0.3)
        elif stance == "contradict":
            stance_conf = min(1.0, raw_sim + 0.25)
        else:
            stance_conf = raw_sim * 0.7
        
        publisher = None
        if r.get("url"):
            try:
                publisher = r.get("url").split("/")[2]
            except Exception:
                publisher = None
        
        evidence.append({
            "url": r.get("url"),
            "publisher": publisher,
            "text": r.get("text"),
            "snippet": snippet_text,
            "semantic_sim": sim,
            "stance": stance,
            "stance_conf": float(stance_conf)
        })
    
    raw_label, percent, summary, breakdown = aggregate_verdict(claim, evidence, verbose=True)
    mapped = map_percent_to_label(percent, raw_label)
    
    return {
        "ok": True,
        "input": claim,
        "verdict_percent": round(percent, 2),
        "verdict_label": mapped["label"],
        "verdict_machine_label": mapped["machine_label"],
        "verdict_raw_label": raw_label,
        "verdict_summary": summary,
        "ranked": ranked,
        "evidence": evidence,
        "aggregate_breakdown": breakdown
    }

@app.post("/admin/reload")
async def admin_reload():
    return {"ok": True, "message": "Improved stance detection loaded"}