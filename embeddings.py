"""Turns text into vectors (embeddings) so we can search by meaning, not just by words."""

import hashlib
import os
from pathlib import Path

import numpy as np

import config

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small").strip()
CACHE_DIR = config.BASE_DIR / ".cache"


def _client():
    from openai import OpenAI

    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise config.MissingKeyError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=key)


def _normalise(matrix: np.ndarray) -> np.ndarray:
    """Make every vector length 1, so 'inner product' equals cosine similarity."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return (matrix / np.maximum(norms, 1e-12)).astype("float32")


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return one normalised vector per text (a 2-D float32 array)."""
    response = _client().embeddings.create(model=EMBED_MODEL, input=texts)
    vectors = np.array([item.embedding for item in response.data], dtype="float32")
    return _normalise(vectors)


def embed_cached(texts: list[str]) -> np.ndarray:
    """Same as embed_texts, but saved on disk. Re-embeds only when the texts change."""
    fingerprint = hashlib.sha256((EMBED_MODEL + "\n".join(texts)).encode("utf-8")).hexdigest()[:16]
    cache_file = CACHE_DIR / f"vectors_{fingerprint}.npy"
    if cache_file.exists():
        return np.load(cache_file)
    vectors = embed_texts(texts)
    CACHE_DIR.mkdir(exist_ok=True)
    np.save(cache_file, vectors)
    return vectors