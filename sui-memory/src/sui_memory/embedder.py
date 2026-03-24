"""Embedding model wrapper using Ruri v3-30m (Japanese-optimized, 256-dim)."""

from __future__ import annotations

import struct

import numpy as np

MODEL_NAME = "cl-nagoya/ruri-v3-30m"
EMBEDDING_DIM = 256
QUERY_PREFIX = "検索クエリ: "
DOCUMENT_PREFIX = "検索文書: "

_model = None


def _get_model():
    """Lazy-load the SentenceTransformer model (singleton)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME, device="cpu")
    return _model


def encode_documents(texts: list[str], *, batch_size: int = 32) -> list[np.ndarray]:
    """Encode document texts for storage. Returns list of normalized 256-dim vectors."""
    if not texts:
        return []
    model = _get_model()
    prefixed = [DOCUMENT_PREFIX + t for t in texts]
    embeddings = model.encode(prefixed, batch_size=batch_size, normalize_embeddings=True)
    return [emb for emb in embeddings]


def encode_query(text: str) -> np.ndarray:
    """Encode a query text for search. Returns normalized 256-dim vector."""
    model = _get_model()
    prefixed = QUERY_PREFIX + text
    embedding = model.encode([prefixed], normalize_embeddings=True)
    return embedding[0]


def to_blob(embedding: np.ndarray) -> bytes:
    """Convert numpy embedding to SQLite BLOB (float32 bytes)."""
    return embedding.astype(np.float32).tobytes()


def from_blob(blob: bytes) -> np.ndarray:
    """Convert SQLite BLOB back to numpy embedding."""
    return np.frombuffer(blob, dtype=np.float32)
