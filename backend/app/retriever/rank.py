from app.models.embedder import Embedder
import numpy as np

embedder = Embedder()

async def rank_snippets(claim: str, candidates: list, top_k: int = 20):
    """
    candidates: [{url, text}]
    returns: list of top_k items with additional 'score'
    """
    texts = [c["text"] for c in candidates]
    # embed in batches
    emb_texts = embedder.embed_texts(texts)
    emb_claim = embedder.embed_texts([claim])[0]
    # cosine similarity
    sims = (emb_texts @ emb_claim) / (np.linalg.norm(emb_texts, axis=1) * (np.linalg.norm(emb_claim) + 1e-12))
    # pick top_k
    idx = np.argsort(sims)[-top_k:][::-1]
    top = []
    for i in idx:
        item = candidates[int(i)].copy()
        item["score"] = float(sims[int(i)])
        top.append(item)
    return top
