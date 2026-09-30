"""Corpus → chunks → embeddings pipeline.

Writes chunks + embeddings to a local parquet checkpoint BEFORE loading to Savanna,
so a graph-load failure never triggers re-embedding.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Iterator

import pandas as pd
from loguru import logger
from tqdm import tqdm

from core.config import ROOT
from core.llm import embed
from ingest.chunker import chunk_text


CORPUS = ROOT / "data" / "corpus.jsonl"
CHUNKS_PATH = ROOT / ".cache" / "chunks.parquet"
EMB_PATH = ROOT / ".cache" / "embeddings.parquet"


def iter_docs() -> Iterator[dict]:
    with CORPUS.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def build_chunks() -> pd.DataFrame:
    rows: list[dict] = []
    for doc in tqdm(iter_docs(), desc="chunk", total=2951):
        pieces = chunk_text(doc["text"], size=512, overlap=64)
        for i, txt in enumerate(pieces):
            rows.append({
                "chunk_id": f"{doc['doc_id']}#{i}",
                "doc_id": doc["doc_id"],
                "ord": i,
                "text": txt,
                "title": doc["title"],
            })
    df = pd.DataFrame(rows)
    df.to_parquet(CHUNKS_PATH, index=False)
    logger.info(f"wrote {len(df)} chunks -> {CHUNKS_PATH}")
    return df


def build_embeddings(batch_size: int = 32) -> None:
    if not CHUNKS_PATH.exists():
        build_chunks()
    df = pd.read_parquet(CHUNKS_PATH)
    logger.info(f"embedding {len(df)} chunks...")

    all_emb: list[list[float]] = []
    for start in tqdm(range(0, len(df), batch_size), desc="embed"):
        batch = df["text"].iloc[start:start + batch_size].tolist()
        e = embed(batch, input_type="passage")
        all_emb.extend(e)

    dim = len(all_emb[0]) if all_emb else 0
    logger.info(f"emb dim = {dim}")

    df["embedding"] = [struct.pack(f"{dim}f", *v).hex() for v in all_emb]
    df["dim"] = dim
    df.to_parquet(EMB_PATH, index=False)
    logger.info(f"wrote embeddings -> {EMB_PATH}")


def load_embeddings() -> tuple[pd.DataFrame, "np.ndarray"]:
    import numpy as np
    df = pd.read_parquet(EMB_PATH)
    dim = int(df["dim"].iloc[0])
    arr = np.stack([
        np.frombuffer(bytes.fromhex(h), dtype=np.float32) for h in df["embedding"]
    ])
    # normalize for cosine
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    arr = arr / np.clip(norms, 1e-9, None)
    return df.drop(columns=["embedding"]), arr


if __name__ == "__main__":
    build_chunks()
    build_embeddings()
