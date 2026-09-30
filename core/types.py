from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Pipeline = Literal["rag", "graphrag", "agentic"]
QType = Literal["lookup", "aggregation", "temporal", "multi_hop", "superlative"]


class TokenAccounting(BaseModel):
    input: int = 0
    output: int = 0
    cached: int = 0


class AnswerObject(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    pipeline: Pipeline
    qid: str | None = None
    tokens: TokenAccounting = Field(default_factory=TokenAccounting)
    latency_ms: int = 0
    trace: list[dict[str, Any]] = Field(default_factory=list)
    budget_exceeded: bool = False
    error: str | None = None


class ComposedAnswer(BaseModel):
    """Strict schema the LLM must return."""

    answer: str
    citations: list[str] = Field(default_factory=list)
