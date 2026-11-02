"""FAISS index over the knowledge-base passages: find the passages closest in meaning to a question."""

import faiss
import numpy as np

from embeddings import embed_cached, embed_texts


class VectorIndex:
    def __init__(self, texts: list[str]):
        vectors = embed_cached(texts)              # one vector per passage (cached on disk)
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)                    # put all passage vectors into FAISS

    def search(self, query: str, top_k: int = 5):
        """Return [(passage_number, similarity), ...] best first."""
        query_vector = embed_texts([query])        # the question becomes a vector too
        scores, ids = self.index.search(query_vector, top_k)
        return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i != -1]