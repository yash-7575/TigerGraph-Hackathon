"""Answer & retrieval scorers."""

from __future__ import annotations

import re
import unicodedata


_NUM_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
}

_ARTICLES = {"the", "a", "an"}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.casefold()
    s = re.sub(r"[^\w\s]", " ", s)
    tokens = [t for t in s.split() if t and t not in _ARTICLES]
    tokens = [_NUM_WORDS.get(t, t) for t in tokens]
    return " ".join(tokens).strip()


def exact_match(prediction: str, gold: list[str]) -> bool:
    pn = normalize(prediction)
    for g in gold:
        gn = normalize(g)
        if pn == gn:
            return True
        # containment - useful when model returns "Chen Ding won gold"
        if gn and gn in pn.split():
            return True
        # word-set containment for names like "Chen Ding" in "chen ding"
        if gn and gn in pn:
            return True
    return False


def recall_at_k(retrieved: list[str], gold: list[str]) -> float:
    if not gold:
        return 1.0
    gold_set = set(gold)
    retrieved_set = set(retrieved)
    return len(gold_set & retrieved_set) / len(gold_set)


def any_hit(retrieved: list[str], gold: list[str]) -> bool:
    if not gold:
        return True
    return bool(set(retrieved) & set(gold))
