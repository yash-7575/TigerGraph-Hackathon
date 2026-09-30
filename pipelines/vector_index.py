"""Local numpy-backed cosine vector search over corpus chunks.

Loaded once at import; shared across pipelines.
"""

from __future__ import annotations

import threading
from functools import lru_cache
from typing import Any

import numpy as np

from core.llm import embed
from ingest.embedder import load_embeddings


_lock = threading.Lock()


@lru_cache(maxsize=1)
def _index() -> tuple[Any, np.ndarray]:
    df, mat = load_embeddings()
    return df, mat


def search(query: str, k: int = 8, doc_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """Return top-k chunks: [{chunk_id, doc_id, ord, title, text, score}]."""
    df, mat = _index()
    q = embed([query], input_type="query")[0]
    qv = np.array(q, dtype=np.float32)
    qv = qv / max(float(np.linalg.norm(qv)), 1e-9)
    scores = mat @ qv

    if doc_ids:
        mask = df["doc_id"].isin(doc_ids).to_numpy()
        scores = np.where(mask, scores, -1.0)

    idx = np.argpartition(-scores, min(k, len(scores) - 1))[:k]
    idx = idx[np.argsort(-scores[idx])]

    out: list[dict[str, Any]] = []
    for i in idx:
        i = int(i)
        row = df.iloc[i]
        out.append({
            "chunk_id": row["chunk_id"],
            "doc_id": row["doc_id"],
            "ord": int(row["ord"]),
            "title": row["title"],
            "text": row["text"],
            "score": float(scores[i]),
        })
    return out
