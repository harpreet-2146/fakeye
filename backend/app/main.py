# app/main.py
import os
import logging
from typing import List

from dotenv import load_dotenv
load_dotenv()

from app.retriever.improved_stance import simple_stance_heuristic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from app.retriever.rank import rank_snippets
from app.retriever.aggregate import aggregate_verdict

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
            return {"label": "Conflicting — Mixed Signals", "machine_label": "mixture"}
        else:
            return {"label": "Conflicting but leaning", "machine_label": "mixture_high_confidence"}
    if rl == "true":
        if p >= 85:
            return {"label": "Definitely True", "machine_label": "definitely_true"}
        elif p >= 65:
            return {"label": "Likely True", "machine_label": "likely_true"}
        elif p >= 40:
            return {"label": "Possibly True", "machine_label": "possibly_true"}
        else:
            return {"label": "Uncertain — needs review", "machine_label": "uncertain"}
    if rl == "false":
        if p <= 15:
            return {"label": "Definitely False", "machine_label": "definitely_false"}
        elif p <= 35:
            return {"label": "Likely False", "machine_label": "likely_false"}
        elif p <= 60:
            return {"label": "Possibly False", "machine_label": "possibly_false"}
        else:
            return {"label": "Uncertain — needs review", "machine_label": "uncertain"}
    return {"label": "Uncertain — needs review", "machine_label": "uncertain"}

@app.get("/health")
async def health():
    return {"ok": True, "serpapi_set": bool(SERPAPI_API_KEY)}

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
        raise HTTPException(502, f"Search failed: {e}")
    organic = json_resp.get("organic_results") or json_resp.get("news_results") or []
    candidates = []
    for hit in organic:
        title = hit.get("title") or ""
        snippet = hit.get("snippet") or hit.get("description") or ""
        url = hit.get("link") or hit.get("url")
        candidates.append({"url": url, "title": title, "snippet": snippet, "text": f"{title} {snippet}".strip()})
    try:
        ranked = await rank_snippets(claim, candidates, top_k=min(10, len(candidates)))
    except Exception:
        ranked = []
        for c in candidates[:5]:
            ranked.append({**c, "score": 0.0, "raw_sim": 0.0})
    evidence = []
    for r in ranked:
        sim = float(r.get("score", 0.0) or 0.0)
        raw_sim = float(r.get("raw_sim", sim) or sim)
        snippet_text = r.get("snippet") or r.get("text") or ""
        stance = simple_stance_heuristic(snippet_text, claim)
        stance_conf = raw_sim if raw_sim is not None else sim
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
            "stance_conf": float(stance_conf or 0.0)
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

# ---- DEBUG endpoint: returns detailed breakdown from aggregator
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
        raise HTTPException(502, f"Search failed: {e}")
    organic = json_resp.get("organic_results") or json_resp.get("news_results") or []
    candidates = []
    for hit in organic:
        title = hit.get("title") or ""
        snippet = hit.get("snippet") or hit.get("description") or ""
        url = hit.get("link") or hit.get("url")
        candidates.append({"url": url, "title": title, "snippet": snippet, "text": f"{title} {snippet}".strip()})
    try:
        ranked = await rank_snippets(claim, candidates, top_k=min(10, len(candidates)))
    except Exception as e:
        logger.exception("ranking failed: %s", e)
        ranked = []
        for c in candidates[:5]:
            ranked.append({**c, "score": 0.0, "raw_sim": 0.0})

    evidence = []
    for r in ranked:
        sim = float(r.get("score", 0.0) or 0.0)
        raw_sim = float(r.get("raw_sim", sim) or sim)
        snippet_text = r.get("snippet") or r.get("text") or ""
        stance = simple_stance_heuristic(snippet_text, claim)
        stance_conf = raw_sim if raw_sim is not None else sim
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
            "stance_conf": float(stance_conf or 0.0)
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
    return {"ok": True, "message": "No model to reload (search + heuristics)."}

# # app/main.py
# import os
# import logging
# import asyncio
# from typing import Optional

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import requests

# # create app BEFORE adding middleware
# app = FastAPI(title="fakeye-api-no-hf")

# # allow local dev origins — change to your production origin when deploying
# origins = [
#     "http://localhost",
#     "http://localhost:3000",
#     "http://127.0.0.1",
#     "http://127.0.0.1:3000",
#     "null",
#     # add your deployed frontend URL(s) here when ready
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# logger = logging.getLogger("uvicorn.error")

# # Config: set SERPAPI_API_KEY in env or OS
# SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
# if not SERPAPI_API_KEY:
#     logger.warning("SERPAPI_API_KEY not found in env. /predict will fail until you set it.")

# # Simple request model
# class PredictRequest(BaseModel):
#     text: str

# # Simple health check
# @app.get("/health")
# async def health():
#     return {"ok": True, "serpapi_set": bool(SERPAPI_API_KEY)}

# # Simple helper: search via SerpApi
# def serp_search(query: str, api_key: str, num: int = 10):
#     """
#     Uses SerpApi search endpoint to fetch search results JSON.
#     Returns the raw JSON on success or raises Exception on failure.
#     """
#     url = "https://serpapi.com/search.json"
#     params = {
#         "q": query,
#         "api_key": api_key,
#         "num": num
#     }
#     r = requests.get(url, params=params, timeout=15)
#     r.raise_for_status()
#     return r.json()

# def heuristic_fake_score_from_serp(json_resp: dict) -> dict:
#     """
#     Heuristic to guess whether the text is likely real or suspicious:
#     - If multiple recognized news sources or many results -> likely real
#     - If zero results or only obscure sources -> suspicious
#     This is a heuristic, not a model.
#     """
#     organic = json_resp.get("organic_results") or json_resp.get("news_results") or []
#     count = len(organic)
#     top_hosts = set()
#     for hit in organic[:10]:
#         # different SerpApi responses store link/title slightly differently
#         link = hit.get("link") or hit.get("url") or ""
#         # extract host simple way
#         if link:
#             try:
#                 host = link.split("/")[2]
#                 top_hosts.add(host)
#             except Exception:
#                 pass

#     # very naive credibility heuristic
#     credible_indicators = 0
#     for host in top_hosts:
#         # common large outlets; expand list as you like
#         if any(x in host for x in ("nytimes", "bbc", "theguardian", "reuters", "apnews", "washingtonpost", "cnn", "hindustantimes", "timesofindia", "economist")):
#             credible_indicators += 1

#     score = {
#         "result_count": count,
#         "distinct_hosts": len(top_hosts),
#         "credible_host_count": credible_indicators
#     }

#     # decision threshold (tweak as needed)
#     if score["result_count"] >= 3 and score["credible_host_count"] >= 1:
#         label = "likely_real"
#     elif score["result_count"] >= 1:
#         label = "uncertain"
#     else:
#         label = "suspicious"

#     return {"label": label, "score": score}

# @app.post("/predict")
# async def predict(req: PredictRequest):
#     if not SERPAPI_API_KEY:
#         raise HTTPException(status_code=500, detail="SERPAPI_API_KEY not set in server environment.")

#     text = req.text.strip()
#     if not text:
#         raise HTTPException(status_code=400, detail="Empty text provided.")

#     # If the user provides a URL, search using the URL; otherwise use the headline/text.
#     query = text
#     try:
#         # call SerpApi (blocking) — kept simple
#         json_resp = serp_search(query, SERPAPI_API_KEY, num=10)
#     except requests.RequestException as e:
#         logger.exception("SerpApi request failed: %s", e)
#         raise HTTPException(status_code=502, detail=f"SerpApi error: {e}")

#     verdict = heuristic_fake_score_from_serp(json_resp)
#     # optional: include top snippets for debugging
#     snippets = []
#     for hit in (json_resp.get("organic_results") or [])[:5]:
#         snippets.append({
#             "title": hit.get("title"),
#             "link": hit.get("link") or hit.get("url"),
#             "snippet": hit.get("snippet") or hit.get("description")
#         })

#     return {
#         "ok": True,
#         "input": text,
#         "verdict": verdict["label"],
#         "verdict_score": verdict["score"],
#         "top_matches": snippets
#     }

# @app.post("/admin/reload")
# async def admin_reload():
#     # no-op here, but kept for compatibility with your UI
#     return {"ok": True, "message": "No model to reload (Hugging Face disabled)."}
