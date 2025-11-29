# app/main.py
import os
import logging
import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

# create app BEFORE adding middleware
app = FastAPI(title="fakeye-api-no-hf")

# allow local dev origins — change to your production origin when deploying
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "null",
    # add your deployed frontend URL(s) here when ready
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn.error")

# Config: set SERPAPI_API_KEY in env or OS
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    logger.warning("SERPAPI_API_KEY not found in env. /predict will fail until you set it.")

# Simple request model
class PredictRequest(BaseModel):
    text: str

# Simple health check
@app.get("/health")
async def health():
    return {"ok": True, "serpapi_set": bool(SERPAPI_API_KEY)}

# Simple helper: search via SerpApi
def serp_search(query: str, api_key: str, num: int = 10):
    """
    Uses SerpApi search endpoint to fetch search results JSON.
    Returns the raw JSON on success or raises Exception on failure.
    """
    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "api_key": api_key,
        "num": num
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def heuristic_fake_score_from_serp(json_resp: dict) -> dict:
    """
    Heuristic to guess whether the text is likely real or suspicious:
    - If multiple recognized news sources or many results -> likely real
    - If zero results or only obscure sources -> suspicious
    This is a heuristic, not a model.
    """
    organic = json_resp.get("organic_results") or json_resp.get("news_results") or []
    count = len(organic)
    top_hosts = set()
    for hit in organic[:10]:
        # different SerpApi responses store link/title slightly differently
        link = hit.get("link") or hit.get("url") or ""
        # extract host simple way
        if link:
            try:
                host = link.split("/")[2]
                top_hosts.add(host)
            except Exception:
                pass

    # very naive credibility heuristic
    credible_indicators = 0
    for host in top_hosts:
        # common large outlets; expand list as you like
        if any(x in host for x in ("nytimes", "bbc", "theguardian", "reuters", "apnews", "washingtonpost", "cnn", "hindustantimes", "timesofindia", "economist")):
            credible_indicators += 1

    score = {
        "result_count": count,
        "distinct_hosts": len(top_hosts),
        "credible_host_count": credible_indicators
    }

    # decision threshold (tweak as needed)
    if score["result_count"] >= 3 and score["credible_host_count"] >= 1:
        label = "likely_real"
    elif score["result_count"] >= 1:
        label = "uncertain"
    else:
        label = "suspicious"

    return {"label": label, "score": score}

@app.post("/predict")
async def predict(req: PredictRequest):
    if not SERPAPI_API_KEY:
        raise HTTPException(status_code=500, detail="SERPAPI_API_KEY not set in server environment.")

    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text provided.")

    # If the user provides a URL, search using the URL; otherwise use the headline/text.
    query = text
    try:
        # call SerpApi (blocking) — kept simple
        json_resp = serp_search(query, SERPAPI_API_KEY, num=10)
    except requests.RequestException as e:
        logger.exception("SerpApi request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"SerpApi error: {e}")

    verdict = heuristic_fake_score_from_serp(json_resp)
    # optional: include top snippets for debugging
    snippets = []
    for hit in (json_resp.get("organic_results") or [])[:5]:
        snippets.append({
            "title": hit.get("title"),
            "link": hit.get("link") or hit.get("url"),
            "snippet": hit.get("snippet") or hit.get("description")
        })

    return {
        "ok": True,
        "input": text,
        "verdict": verdict["label"],
        "verdict_score": verdict["score"],
        "top_matches": snippets
    }

@app.post("/admin/reload")
async def admin_reload():
    # no-op here, but kept for compatibility with your UI
    return {"ok": True, "message": "No model to reload (Hugging Face disabled)."}
