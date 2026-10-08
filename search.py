import numpy as np
from ingestion.embeddings import get_model

# Tune on a few in-scope / out-of-scope questions. bge-small: ~0.45-0.55 works.
MIN_SCORE = 0.50


def search(index, chunks, query, k=6):
    q = get_model().encode(
        ["Represent this sentence for searching relevant passages: " + query],
        normalize_embeddings=True)
    scores, ids = index.search(np.array(q, dtype="float32"), k)
    return [(chunks[i], float(s)) for i, s in zip(ids[0], scores[0]) if i >= 0]


def is_supported(hits):
    return bool(hits) and hits[0][1] >= MIN_SCORE
