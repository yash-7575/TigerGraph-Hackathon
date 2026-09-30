# Agentic GraphRAG on TigerGraph

TigerGraph Hackathon Round 1 submission. Three interchangeable pipelines — **RAG**, **GraphRAG**, and **Agentic GraphRAG** — over a 2,951-doc Wikipedia (Olympics-heavy) corpus, benchmarked side by side on 100 public + 50 hidden questions.

## Results (headline)

Run `make dashboard` after `make bench` to render `docs/index.html`. Latest numbers live there.

| Pipeline | Accuracy | Median tokens | Median latency | Notes |
|---|---|---|---|---|
| RAG | (see dashboard) | | | Vector search + LLM |
| GraphRAG | (see dashboard) | | | Entity-linked seeds + vector expansion + LLM |
| Agentic | (see dashboard) | | | Tool-calling loop (entity_link → graph_hop → vector_search → aggregate → answer), budget-capped |

## Architecture

```
Question
   │
   ├─ RAG        → vector_search(k=8) → compose(answer, citations)
   │
   ├─ GraphRAG   → entity_link → seed docs → vector_search(seed_ids) → doc_fetch → compose
   │
   └─ Agentic    → orchestrator loop {plan → tool → evaluate} × ≤8 steps, 30k-token cap
                     tools: entity_link, vector_search, doc_fetch, aggregate, answer
                     fallback: graphrag on budget exhaustion
```

See `TECHNICAL_DESIGN.md` for full design, `PRD.md` for scope, `SRS.md` for requirements.

## Setup

Prereqs: Python 3.12, ~4GB disk, NVIDIA NIM API key (free tier, https://build.nvidia.com), TigerGraph Savanna workspace + database secret.

```bash
git clone <this repo>
cd agentic-graphrag-tigergraph

cp .env.example .env
# fill in NVIDIA_API_KEY, TG_HOST, TG_SECRET

make install         # pip install --user -r requirements.txt
make smoke           # sanity-check NVIDIA endpoints
make ingest          # chunk corpus, embed with nemotron-3-embed-1b, write .cache/embeddings.parquet
make bench           # run all three pipelines on 100 public questions
make hidden          # run agentic on 50 hidden questions → results/agentic/*.json
make dashboard       # build docs/index.html
```

Corpus + questions are symlinked from `hackathon-resources-*/hackathon-resources/`. Drop the release ZIP in the repo root and re-link if needed.

## LLM stack

All calls go through the NVIDIA NIM OpenAI-compatible endpoint (`https://integrate.api.nvidia.com/v1`). Free tier: 40 RPM, no credit card.

| Role | Model | Notes |
|---|---|---|
| Orchestrator + composer | `openai/gpt-oss-20b` | Reasoning + tool calls, ~1s latency |
| Sub-agents | `openai/gpt-oss-20b` | Same model; cheap to reuse |
| Embeddings | `nvidia/nemotron-3-embed-1b` | 2048 dim, cosine |

Configured in `.env` and `core/config.py`. Swap models via env var — no code change.

## Caching + cost

- Every LLM + embed call SQLite-cached in `.cache/llm.sqlite` by `sha256(model, messages, tools, params)`.
- Rerunning the bench after a code fix costs 0 NVIDIA credits (cache hit).
- Per-pipeline token budget: 4k (RAG) / 8k (GraphRAG) / 30k (Agentic, 8-step cap).

## Repo layout

```
core/           # config, LLM client (cache+retry+rate limit), embed client, types
ingest/         # chunker, embedder, corpus loader
graph/          # GSQL schema (for Savanna traversal in R2)
pipelines/
├── rag.py                 # baseline
├── graphrag.py            # entity-linked seeds + vector expansion
├── vector_index.py        # local numpy cosine store
├── tools/                 # entity_link, doc_store, (graph_hop → R2)
└── agentic/orchestrator.py
bench/
├── run.py                 # parallel harness
├── scorers.py             # exact-match + recall@K
└── dashboard_build.py
docs/           # index.html dashboard, architecture diagram
tests/          # scorers + chunker unit tests
```

## Design notes

- **Local vector index over Savanna vector**: gives sub-second retrieval and avoids conditional syntax risk. Savanna handles structured entity traversal in Round 2.
- **Deterministic aggregation**: agent's `aggregate` tool does Python-side count/sum/min/max — the LLM is never asked to count.
- **Citation guard**: every answer's citations are intersected with observed doc_ids from the retrieval trace. Hallucinated ids are dropped before scoring.
- **Prompt-injection defense**: all retrieved text wrapped in `<untrusted>…</untrusted>`; system prompt states that inside content is data, not instructions.
- **Round-2 hooks**: every fact edge reserves `asserted_at`, `source_doc_id`, `confidence`, and a `SUPERSEDES` edge type is in the schema for conflict resolution.

## Attribution

Corpus derived from English Wikipedia articles, CC BY-SA 4.0. Source URLs preserved on every document.

## License

MIT (this codebase). Corpus content retains its Wikipedia license.
