from sentence_transformers import SentenceTransformer
import numpy as np

class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts):
        # returns numpy array
        embs = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-12)
