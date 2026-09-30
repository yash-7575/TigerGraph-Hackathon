"""Local doc + chunk lookup — used as the primary evidence store.

The graph enriches this with structured facts, but for citations + text
retrieval we go straight to the corpus (fast + no Savanna dep).
"""

from __future__ import annotations

import json
import threading
from functools import lru_cache
from typing import Any

from core.config import ROOT


@lru_cache(maxsize=1)
def _docs() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    with (ROOT / "data" / "corpus.jsonl").open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out[d["doc_id"]] = d
    return out


def doc_fetch(doc_id: str, max_chars: int = 4000) -> dict[str, Any]:
    d = _docs().get(doc_id)
    if not d:
        return {"doc_id": doc_id, "found": False}
    text = d["text"]
    if len(text) > max_chars:
        text = text[:max_chars] + "…[truncated]"
    return {
        "doc_id": d["doc_id"],
        "title": d["title"],
        "url": d.get("url", ""),
        "wikidata_qid": d.get("wikidata_qid"),
        "text": text,
        "found": True,
    }


def doc_all() -> dict[str, dict[str, Any]]:
    return _docs()
