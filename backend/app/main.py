# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Use package imports
from app.schemas.request import ClaimRequest
from app.schemas.response import ClaimResponse
from app.retriever.search import search_urls
from app.retriever.scrape import fetch_and_extract
from app.retriever.rank import rank_snippets
from app.retriever.stance import predict_stance
from app.retriever.aggregate import aggregate_verdict
from app.utils.queries import generate_queries

import asyncio

app = FastAPI(title="Fakeye Claim Checker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/check-claim", response_model=ClaimResponse)
async def check_claim(req: ClaimRequest):
    claim = req.claim.strip()
    if not claim:
        raise HTTPException(status_code=400, detail="Claim is empty")

    # 1) Generate queries
    queries = generate_queries(claim)

    # 2) Search URLs (gather unique)
    urls = []
    for q in queries:
        try:
            found = await search_urls(q)
        except Exception:
            found = []
        for u in found:
            if u not in urls:
                urls.append(u)
            if len(urls) >= 20:
                break
        if len(urls) >= 20:
            break

    if not urls:
        return {"verdict": "Unverifiable", "confidence": 15, "summary": "No sources found.", "evidence": []}

    # 3) Fetch & extract paragraphs concurrently
    tasks = [fetch_and_extract(u) for u in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    candidates = []
    for u, res in zip(urls, results):
        if isinstance(res, Exception) or not res:
            continue
        for p in res:
            if len(p.split()) < 8:
                continue
            candidates.append({"url": u, "text": p})

    if not candidates:
        return {"verdict": "Unverifiable", "confidence": 20, "summary": "No usable text extracted.", "evidence": []}

    # 4) Rank by semantic similarity
    top_candidates = await rank_snippets(claim, candidates)

    # 5) Run NLI/stance on top candidates
    evidence = []
    for item in top_candidates:
        nli_res = predict_stance(claim, item["text"])
        # determine stance label and confidence
        entail = nli_res.get("entailment", 0.0)
        contradict = nli_res.get("contradiction", 0.0)
        neutral = nli_res.get("neutral", 0.0)
        if entail >= 0.6:
            stance = "support"
            stance_conf = entail
        elif contradict >= 0.6:
            stance = "contradict"
            stance_conf = contradict
        else:
            stance = "neutral"
            stance_conf = max(entail, contradict, neutral)

        evidence.append({
            "url": item["url"],
            "publisher": item.get("publisher"),
            "snippet": item["text"][:800],
            "stance": stance,
            "stance_conf": float(stance_conf),
            "semantic_sim": float(item.get("score", 0.0))
        })

    # 6) Aggregate into verdict
    verdict, confidence, summary = aggregate_verdict(claim, evidence)

    return {"verdict": verdict, "confidence": int(confidence), "summary": summary, "evidence": evidence[:10]}

