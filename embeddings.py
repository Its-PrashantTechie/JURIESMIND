import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model


def build_index(chunks):
    vecs = get_model().encode([c["text"] for c in chunks], normalize_embeddings=True)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(np.array(vecs, dtype="float32"))
    return index
