# app/retriever/rank.py
import numpy as np
from app.models.embedder import Embedder

embedder = Embedder()

async def rank_snippets(claim: str, candidates: list, top_k: int = 20):
    texts = [c.get("text", "") or "" for c in candidates]

    # Try embeddings
    try:
        emb_texts = np.asarray(embedder.embed_texts(texts), float)
        emb_claim = np.asarray(embedder.embed_texts([claim])[0], float)

        sims = np.zeros(len(texts), float)
        denom = np.linalg.norm(emb_texts, axis=1) * (np.linalg.norm(emb_claim) + 1e-12)
        valid = denom > 0
        sims[valid] = (emb_texts[valid] @ emb_claim) / denom[valid]

    except Exception:
        sims = np.zeros(len(texts), float)

    # Fallback if degenerate
    if np.nanmax(sims) <= 1e-6:
        claim_words = [w.lower() for w in claim.split() if len(w) > 3]
        sims = np.zeros(len(texts), float)
        for i, t in enumerate(texts):
            t_l = t.lower()
            matches = sum(1 for w in claim_words if w in t_l)
            sims[i] = matches / max(1, len(claim_words))
        sims *= 0.4

    # Normalize sims
    mn, mx = float(np.nanmin(sims)), float(np.nanmax(sims))
    if mx - mn > 1e-12:
        norm = (sims - mn) / (mx - mn)
    else:
        norm = np.clip(sims, 0, 1)

    idx = np.argsort(norm)[-min(top_k, len(norm)):][::-1]

    top = []
    for i in idx:
        item = candidates[int(i)].copy()
        item["score"] = float(norm[int(i)])
        item["raw_sim"] = float(sims[int(i)])
        top.append(item)

    return top
