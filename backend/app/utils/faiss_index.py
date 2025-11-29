# app/utils/faiss_index.py
import os, json, faiss, numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMB_DIM = 384  # depends on model
INDEX_DIR = Path("data/faiss")
INDEX_FILE = INDEX_DIR / "index.faiss"
META_FILE = INDEX_DIR / "meta.json"

class FaissIndex:
    def __init__(self, model_name=MODEL):
        self.model = SentenceTransformer(model_name)
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        if INDEX_FILE.exists() and META_FILE.exists():
            self.index = faiss.read_index(str(INDEX_FILE))
            with open(META_FILE, "r", encoding="utf-8") as f:
                self.meta = json.load(f)  # list of {url, text, publisher}
        else:
            self.index = faiss.IndexFlatIP(EMB_DIM)  # cosine via normalized vectors
            self.meta = []

    def add_docs(self, docs):
        """
        docs: list of {'url':..., 'text':..., 'publisher':...}
        """
        texts = [d["text"] for d in docs]
        embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        # normalize for inner product cosine
        norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-10
        embs = embs / norms
        self.index.add(np.array(embs).astype("float32"))
        self.meta.extend(docs)
        self.save()

    def search(self, query, top_k=10):
        q_emb = self.model.encode([query], convert_to_numpy=True)
        q_emb = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-10)
        D, I = self.index.search(q_emb.astype("float32"), top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(self.meta): 
                continue
            m = self.meta[idx].copy()
            m["score"] = float(score)
            results.append(m)
        return results

    def save(self):
        faiss.write_index(self.index, str(INDEX_FILE))
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)
