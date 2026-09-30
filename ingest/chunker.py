"""Token-aware chunking with overlap."""

from __future__ import annotations

import tiktoken


_enc = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, size: int = 512, overlap: int = 64) -> list[str]:
    tokens = _enc.encode(text)
    if not tokens:
        return []
    out: list[str] = []
    step = max(1, size - overlap)
    for start in range(0, len(tokens), step):
        piece = tokens[start:start + size]
        if not piece:
            break
        out.append(_enc.decode(piece))
        if start + size >= len(tokens):
            break
    return out
