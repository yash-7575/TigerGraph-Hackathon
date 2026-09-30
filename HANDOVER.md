# HANDOVER — Agentic GraphRAG on TigerGraph

**Deadline:** 30 Sept 2026 (Unstop cutoff = midnight IST 30 Sept). It's currently 30 Sept 2026 ~23:20 IST at handover — about **30 min to submission** or a same-day resubmit tolerated by the platform.

**Repo root:** `/home/yash/dev/hack/TigerGraph-Hackathon/`
**Not yet pushed to GitHub** — user's `yash-7575` account. Repo name TBD (default: `agentic-graphrag-tigergraph`).

---

## Where you're picking up

Task list (see planner state):

- [x] **CP0** repo scaffold + smoke tests
- [x] **CP1** RAG bench — **DONE**. See numbers below.
- [ ] **CP2** GraphRAG bench (code ready; just needs `python3.12 -m bench.run --pipeline graphrag`)
- [ ] **CP3** Agentic bench + hidden preds
- [ ] **CP4** Dashboard + push GitHub
- [ ] **CP5** Demo video + Unstop submit

Read the full plan at `/home/yash/.claude/plans/implementation-plan-agentic-gentle-boole.md`.

---

## Credentials — already in `.env` (do NOT commit)

```
TG_HOST=https://tg-3db04169-9c1d-45ec-9038-905f9229ece5.tg-2635877100.i.tgcloud.io
TG_SECRET=pfheb22vkgmc17t7b3k0s0hr4om2rphq
TG_GRAPHNAME=xyz
NVIDIA_API_KEY=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
LLM_MODEL_ORCH=openai/gpt-oss-20b
LLM_MODEL_SUB=openai/gpt-oss-20b
EMBED_MODEL=nvidia/nemotron-3-embed-1b
```

`.env` is in `.gitignore`. `.env.example` is committed.

**Verified working:** Savanna connects (v4.2.5, token OK), NVIDIA embed (`nemotron-3-embed-1b` → 2048 dim), NVIDIA chat (`gpt-oss-20b` → tool-calls work).

**Model quirks:** `deepseek-v4.1-flash`, `kimi-k3`, `z-ai/glm-5-3*` all hang or 404 on this free-tier account. `openai/gpt-oss-20b` is the only reliable chat model — it's a reasoning model that puts `<thinking>` in `reasoning_content` and clean answer in `content`. Tool calling supported.

**Rate limit:** free tier is 40 RPM. `core/llm.py` has a 30-RPM token-bucket. Keep `workers ≤ 4`.

---

## What's already coded & tested

### Files that work

```
core/
├── config.py     # loads .env with override=True (shell has empty NVIDIA_API_KEY=)
├── llm.py        # chat() + embed() with SQLite cache + retry + rate limit
├── tg.py         # pyTigerGraph connection helper
└── types.py      # AnswerObject, ComposedAnswer

ingest/
├── chunker.py    # 512 tok / 64 overlap (tiktoken cl100k_base)
└── embedder.py   # builds .cache/chunks.parquet + .cache/embeddings.parquet — DONE, 15,345 chunks × 2048 dim, 249 MB

pipelines/
├── rag.py                       # top-k=8 (16 for aggregation), JSON output w/ regex salvage
├── graphrag.py                  # entity_link seeds → seed-restricted vector search → doc previews → compose
├── vector_index.py              # local numpy cosine (loaded lazily, cached)
├── tools/
│   ├── doc_store.py             # doc_all(), doc_fetch()
│   └── entity_link.py           # exact + rapidfuzz over titles/QIDs
└── agentic/orchestrator.py      # 8-step tool loop; tools: entity_link, vector_search, doc_fetch, aggregate, answer

bench/
├── run.py                       # ThreadPoolExecutor(4), summary.csv + per_qtype.json + run_manifest.json
├── scorers.py                   # NFKC + casefold + number-word + article-strip; exact_match / recall_at_k
└── dashboard_build.py           # static HTML w/ Chart.js
```

### Tests

`python3.12 -m pytest tests/ -v` → 9 passed.

### Data

- `data/corpus.jsonl` (symlink), `data/eval_public.jsonl` (100 Qs), `data/eval_hidden.jsonl` (50 Qs) — all symlinked from `hackathon-resources-*/hackathon-resources/`, gitignored.
- `.cache/embeddings.parquet` — 15,345 chunks embedded, ready to use. **Don't re-run `make ingest`** — it's expensive and cached.
- `.cache/llm.sqlite` — LLM cache. Rerunning benches after code fixes is free.

### RAG bench (100 public Qs) — FINAL

**Overall accuracy: 69%**, recall@K: 57%, median 4,498 in-tokens, ~16s/Q.

| qtype | n | acc | recall | med tokens |
|---|---|---|---|---|
| lookup | 19 | **100%** | 100% | 4.5k |
| temporal | 22 | 86% | 43% | 4.5k |
| multi_hop | 28 | 68% | 75% | 4.5k |
| aggregation | 21 | 57% | 33% | 8.8k |
| superlative | 10 | **0%** | 9% | 4.5k |

0 errors, all citations survived filter. **Superlative is the big loss** — LLM can't find max/min across scattered chunks. Agentic pipeline's `aggregate` tool should recover most of these. Aggregation is second-hardest for the same reason.

---

## What to do next (in order)

### 1. Check RAG bench status

```bash
ls results/rag/*.json | wc -l          # was 31 at handover; goal 100
tail -c 500 /tmp/claude-*/tasks/bfe9j6qfo.output   # tqdm output
```

If still running, wait. If finished (`results/rag/summary.csv` exists):

```bash
python3.12 -c "
import pandas as pd
df = pd.read_csv('results/rag/summary.csv')
print('n:', len(df))
print('acc:', df['correct'].mean())
print(df.groupby('qtype').agg(n=('qid','count'), acc=('correct','mean')).round(2))
"
```

### 2. Run GraphRAG bench

```bash
python3.12 -m bench.run --pipeline graphrag --workers 4
```

Same 100 Qs, uses entity_link + vector. Will take ~10 min.

### 3. Run Agentic bench

```bash
python3.12 -m bench.run --pipeline agentic --workers 2
```

Longer — 8 steps × several LLM calls per Q. Cap workers at 2 to respect rate limit. Expect 20-40 min.

### 4. Run hidden eval (agentic pipeline only)

```bash
python3.12 -m bench.run --pipeline agentic --questions data/eval_hidden.jsonl --workers 2
mv results/agentic results/agentic_public       # (or copy first)
```

Actually the bench writes to `results/{pipeline}/`, so hidden run will overwrite public. Fix: `mv results/agentic results/agentic_hidden` after this run — OR change `bench/run.py` to accept `--out_dir`. Simpler: after step 3 finishes, rename `results/agentic` → `results/agentic_public`, then run hidden.

### 5. Build dashboard

```bash
python3.12 -m bench.dashboard_build
# opens at docs/index.html
```

### 6. Push to GitHub

```bash
gh repo create yash-7575/agentic-graphrag-tigergraph --public --source=. --push --description "TigerGraph Hackathon: agentic GraphRAG with three-way benchmark"
gh workflow list  # (no CI yet — skip)
```

Enable GitHub Pages on `docs/` in repo settings.

### 7. Video + submit

Record 3-5 min demo. Fill Unstop form: repo URL, dashboard URL, brief write-up.

---

## Known blockers / gotchas

1. **Savanna schema push refused** — tried to add vertex with attribute name `type`, TG 4.2.5 rejects reserved word. Rename to `entity_type` and retry:
   ```gsql
   USE GRAPH xyz
   CREATE SCHEMA_CHANGE JOB olympics_init FOR GRAPH xyz {
     ADD VERTEX Document (PRIMARY_ID doc_id STRING, title STRING, url STRING, wikidata_qid STRING) WITH PRIMARY_ID_AS_ATTRIBUTE="true";
     ADD VERTEX Chunk (PRIMARY_ID chunk_id STRING, doc_id STRING, ord UINT, text STRING) WITH PRIMARY_ID_AS_ATTRIBUTE="true";
     ADD VERTEX Entity (PRIMARY_ID qid STRING, name STRING, entity_type STRING) WITH PRIMARY_ID_AS_ATTRIBUTE="true";
     ADD DIRECTED EDGE HAS_CHUNK (FROM Document, TO Chunk, ord UINT);
     ADD DIRECTED EDGE MENTIONS (FROM Document, TO Entity);
   }
   RUN SCHEMA_CHANGE JOB olympics_init
   DROP JOB olympics_init
   ```
   **User rejected this in the last turn — do NOT retry without explicit user OK.** Graph loading is optional for Round 1 submission because RAG + local GraphRAG + agentic already work; Savanna is used only for future R2 traversal. Note in the README that Savanna integration is stubbed and the graph traversal path uses local indices for now.

2. **Openai client key leak:** shell env had `NVIDIA_API_KEY=` empty. `core/config.py` calls `load_dotenv(override=True)` — keep it.

3. **`smoke.py` still references old model names** — safe to ignore. `smoke_nvidia.py` is the working one.

4. **`graph/install_schema.py`** exists but never ran cleanly; `graph/schema.gsql` also uses reserved word `type`. Fix both if you decide to load Savanna after all.

5. **PRD/SRS/TECHNICAL_DESIGN** — committed and complete. Don't rewrite; reference in submission.

---

## Submission checklist (Round 1)

- [ ] `results/rag/summary.csv` — 100 rows
- [ ] `results/graphrag/summary.csv` — 100 rows
- [ ] `results/agentic/summary.csv` — 100 rows (or `results/agentic_public/`)
- [ ] `results/agentic_hidden/*.json` — 50 files, each with `answer` + citations
- [ ] `docs/index.html` — three-pipeline dashboard renders
- [ ] Public GitHub repo
- [ ] README updated with actual result numbers
- [ ] Architecture diagram in `docs/` (export Mermaid from `TECHNICAL_DESIGN.md` — draw.io or mermaid.live works)
- [ ] 3-5 min demo video (upload YouTube unlisted, link in README)
- [ ] Unstop submission form completed

**If short on time, cut in this order:** demo video → GitHub Pages → hidden preds → agentic. The core three-pipeline benchmark on public Qs + dashboard + repo is the minimum viable submission.

---

## Contact

User: **Yash Bhagyawant** (`yash-7575` on GitHub, `yashbhagyawant70@gmail.com`).
Discord: https://discord.gg/eKWm3mbkw2 (post there if you get stuck on hackathon rules).

Good luck. Ship it.
