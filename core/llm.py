"""NVIDIA NIM LLM client with SQLite cache + retry + rate limit."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from openai import OpenAI, APIError, RateLimitError, APITimeoutError

from core.config import ROOT, settings
from core.types import TokenAccounting


CACHE_PATH = ROOT / ".cache" / "llm.sqlite"
CACHE_PATH.parent.mkdir(exist_ok=True)

_lock = threading.Lock()
_client = OpenAI(base_url=settings.nvidia_base_url, api_key=settings.nvidia_api_key)


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_PATH, timeout=30)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS llm_cache (key TEXT PRIMARY KEY, response TEXT, tokens_in INT, tokens_out INT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS embed_cache (key TEXT PRIMARY KEY, embedding BLOB, dim INT)"
    )
    return conn


def _hash(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(json.dumps(p, sort_keys=True, default=str).encode())
    return h.hexdigest()


# Token-bucket rate limiter (40 rpm free tier -> keep some headroom)
class _RateLimiter:
    def __init__(self, rpm: int = 30):
        self.min_interval = 60.0 / rpm
        self.last = 0.0
        self.lock = threading.Lock()

    def wait(self) -> None:
        with self.lock:
            now = time.time()
            wait = self.min_interval - (now - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()


_rl = _RateLimiter(rpm=30)


def chat(
    messages: list[dict[str, Any]],
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    response_format: dict[str, Any] | None = None,
    use_cache: bool = True,
) -> tuple[dict[str, Any], TokenAccounting]:
    """Return (raw_choice_message_as_dict, TokenAccounting). Cached by hash."""
    model = model or settings.llm_model_orch
    key = _hash(model, messages, tools, tool_choice, temperature, max_tokens, response_format)

    if use_cache:
        with _lock, _db() as db:
            row = db.execute(
                "SELECT response, tokens_in, tokens_out FROM llm_cache WHERE key = ?", (key,)
            ).fetchone()
        if row:
            return json.loads(row[0]), TokenAccounting(input=row[1], output=row[2], cached=1)

    last_err: Exception | None = None
    for attempt in range(4):
        try:
            _rl.wait()
            kwargs: dict[str, Any] = dict(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if tools:
                kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice
            if response_format:
                kwargs["response_format"] = response_format
            r = _client.chat.completions.create(**kwargs)
            msg = r.choices[0].message
            payload = {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in (msg.tool_calls or [])
                ]
                if msg.tool_calls
                else None,
            }
            usage = r.usage
            tok = TokenAccounting(
                input=usage.prompt_tokens if usage else 0,
                output=usage.completion_tokens if usage else 0,
            )
            if use_cache:
                with _lock, _db() as db:
                    db.execute(
                        "INSERT OR REPLACE INTO llm_cache VALUES (?,?,?,?)",
                        (key, json.dumps(payload), tok.input, tok.output),
                    )
                    db.commit()
            return payload, tok
        except (RateLimitError, APITimeoutError) as e:
            last_err = e
            time.sleep(2 ** attempt)
        except APIError as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"LLM call failed after retries: {last_err}")


def embed(texts: list[str], model: str | None = None, input_type: str = "passage") -> list[list[float]]:
    """Batch embed; caches per (model, text, input_type)."""
    model = model or settings.embed_model
    out: list[list[float] | None] = [None] * len(texts)
    to_call: list[tuple[int, str, str]] = []

    with _lock, _db() as db:
        for i, t in enumerate(texts):
            key = _hash(model, t, input_type)
            row = db.execute("SELECT embedding, dim FROM embed_cache WHERE key = ?", (key,)).fetchone()
            if row:
                import struct
                dim = row[1]
                out[i] = list(struct.unpack(f"{dim}f", row[0]))
            else:
                to_call.append((i, key, t))

    if to_call:
        # NIM embed batch size limit safety: chunk to 32
        for start in range(0, len(to_call), 32):
            batch = to_call[start:start + 32]
            _rl.wait()
            r = _client.embeddings.create(
                model=model,
                input=[b[2] for b in batch],
                extra_body={"input_type": input_type, "truncate": "END"},
            )
            with _lock, _db() as db:
                import struct
                for (i, key, _), d in zip(batch, r.data):
                    emb = d.embedding
                    out[i] = list(emb)
                    db.execute(
                        "INSERT OR REPLACE INTO embed_cache VALUES (?,?,?)",
                        (key, struct.pack(f"{len(emb)}f", *emb), len(emb)),
                    )
                db.commit()

    return [o for o in out if o is not None]
