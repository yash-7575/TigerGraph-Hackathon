"""Entity linking — surface form -> corpus doc_id / wikidata_qid.

Uses two indexes built from the corpus:
1. Exact match: title -> doc
2. Fuzzy match: rapidfuzz over title strings
"""

from __future__ import annotations

import re
import threading
from functools import lru_cache
from typing import Any

from rapidfuzz import fuzz, process

from pipelines.tools.doc_store import doc_all


_lock = threading.Lock()


def _normalize(s: str) -> str:
    s = re.sub(r"[^\w\s]", " ", s.lower())
    s = re.sub(r"\s+", " ", s).strip()
    return s


@lru_cache(maxsize=1)
def _index() -> tuple[dict[str, str], dict[str, str], list[str]]:
    """Return (title_norm->doc_id, qid->doc_id, list of titles for fuzzy)."""
    title_map: dict[str, str] = {}
    qid_map: dict[str, str] = {}
    titles: list[str] = []
    for d in doc_all().values():
        n = _normalize(d["title"])
        title_map[n] = d["doc_id"]
        titles.append(d["title"])
        qid = d.get("wikidata_qid")
        if qid:
            qid_map[qid] = d["doc_id"]
    return title_map, qid_map, titles


def entity_link(text: str, k: int = 5, min_score: int = 75) -> list[dict[str, Any]]:
    """Return up to k candidates: [{doc_id, title, score}]."""
    title_map, qid_map, titles = _index()

    # 1. exact match
    n = _normalize(text)
    if n in title_map:
        did = title_map[n]
        docs = doc_all()
        return [{
            "doc_id": did,
            "title": docs[did]["title"],
            "qid": docs[did].get("wikidata_qid"),
            "score": 100.0,
        }]

    # 2. fuzzy
    matches = process.extract(text, titles, scorer=fuzz.WRatio, limit=k)
    out: list[dict[str, Any]] = []
    docs = doc_all()
    for title, score, _ in matches:
        if score < min_score:
            continue
        did = title_map[_normalize(title)]
        out.append({
            "doc_id": did,
            "title": title,
            "qid": docs[did].get("wikidata_qid"),
            "score": float(score),
        })
    return out
