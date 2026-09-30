# PRD — Agentic GraphRAG on TigerGraph

## 🛠️ Project Information

| Field | Value |
|---|---|
| Project Name | Agentic GraphRAG on TigerGraph |
| Version | v0.1 |
| Owner | Yash Bhagyawant |
| Date | 29 Sept 2026 |
| Status | 🟣 Draft |
| Project Type | AI/ML — Retrieval-Augmented Agent System |
| Timeline | 29 Sept 2026 → Round 1: 30 Sept 2026 · Round 2: 7 Oct 2026 · Results: 14 Oct 2026 |

---

## 1. 🔍 Problem

**What problem exists?**
Naive RAG collapses on questions that require multi-step reasoning, aggregation, superlatives, or temporal ordering. A single vector-retrieval pass returns loosely related passages and the LLM either hallucinates or gives up. Structured (graph) evidence helps, but a fixed retrieval pipeline still can't decide *what to look up next* when the first pass is incomplete.

**Who experiences it?**
Anyone building question-answering systems over a bounded knowledge base — hackathon judges evaluating our submission, but also analysts, researchers, and product teams who need grounded answers with citations. In this hackathon the persona is the automated + human evaluator scoring 100 public + 50 hidden Wikipedia-based questions.

**What happens if we do nothing?**
Baseline RAG scores poorly on multi_hop (28% of the eval set), aggregation (21%), and superlative (10%) questions — that's ~60% of the benchmark. We'd land outside the top 15 and lose the Round 2 opportunity.

**Existing alternatives:**
- Plain RAG (LangChain / LlamaIndex defaults) — fast, but fails on multi-hop and aggregation.
- Static GraphRAG (Microsoft's blueprint) — better structure, but no ability to *change strategy* mid-question.
- Neither natively benchmarks all three approaches side by side, which the hackathon explicitly demands.

---

## 2. 🎯 Vision & Goals

**Vision:** An agent that investigates a question the way a researcher does — plans, retrieves, evaluates, redirects — and shows exactly where that beats simpler retrieval.

**Goals:**
1. Ship three interchangeable pipelines (RAG, GraphRAG, Agentic GraphRAG) over the same corpus, scored on the same 100 public questions.
2. Beat the RAG baseline by ≥ 20 accuracy points on multi_hop and aggregation via the agentic pipeline.
3. Produce a metrics dashboard that makes the trade-off (accuracy vs token cost vs latency) legible at a glance.

**Success looks like:** A public GitHub repo + demo video + dashboard where judges can see, per question type, which pipeline wins and why — and top-15 finish in Round 1.

---

## 3. 👥 Target Users

**🥇 Primary User — Hackathon Judge / Evaluator**
- Persona: TigerGraph engineer + LLM-as-judge scoring accuracy, completeness, agentic effectiveness, and code quality.
- Core Need: See a working system, verify grounded answers with citations, and read a clean repo end-to-end in under 30 minutes.

**🥈 Secondary User — Future Developer Reusing the Repo**
- Persona: Engineer wanting a reference implementation of agentic GraphRAG on TigerGraph.
- Core Need: A clear README, modular pipelines, and reproducible benchmark harness.

**User Context:** Judges read the README on desktop, run the demo video, spot-check the dashboard HTML, and skim the repo. Cloud-hosted Savanna instance for the graph; everything else runs locally with `uv` or Docker.

---

## 4. ⚡ Core Features

| # | Feature | Description and user value | Priority |
|---|---|---|---|
| 1 | Corpus ingestion → TigerGraph | Chunk, embed, extract entities from 2,951 Wikipedia docs into a Savanna graph + vector index | P0 |
| 2 | RAG baseline pipeline | Vector-only retrieval + LLM answer, for comparison | P0 |
| 3 | GraphRAG pipeline | Entity-link → subgraph traversal → summarize → answer with citations | P0 |
| 4 | Agentic orchestrator | Plan → tool-select → retrieve → evaluate → loop, with per-qtype routing hints | P0 |
| 5 | Benchmark harness | Runs all three pipelines on the same questions, emits per-qtype scores | P0 |
| 6 | Metrics dashboard | Static HTML comparing accuracy, recall@K, tokens, latency across pipelines | P0 |
| 7 | Hidden-eval predictions | Agentic pipeline output on `eval_hidden.jsonl` | P0 |
| 8 | Temporal-conflict hooks | Schema fields (`asserted_at`, `SUPERSEDES`) reserved for Round 2 | P1 |
| 9 | Trace viewer | Per-question trace of agent steps + evidence — helps demo storytelling | P1 |

---

## 5. 📖 User Stories

- [ ] As a **judge**, I want to run one command and see all three pipelines' scores, so that I can verify the benchmark without setting up my own infra.
  - **Acceptance:** Given a fresh clone with API keys set, when I run `make bench`, then per-pipeline `summary.csv` files land in `results/` within 20 minutes.
- [ ] As a **judge**, I want every answer to cite the `doc_id`s it used, so that I can audit grounding.
  - **Acceptance:** Given any question in `eval_public`, when the agent answers, then the response object contains ≥ 1 citation and each cited doc appears in the retrieval trace.
- [ ] As a **judge**, I want to see *why* the agent chose its next step, so that I can score agentic effectiveness.
  - **Acceptance:** Given any question, when the agent runs, then its trace records `{step, tool, args, evidence_delta, sufficient?}` for every iteration.
- [ ] As a **teammate**, I want to swap the LLM or embedding model with one env var, so that we can cost-tune without refactoring.
  - **Acceptance:** Given `LLM_MODEL` and `EMBED_MODEL` set, when I re-run any pipeline, then it picks up the new models with no code change.

---

## 6. 🧱 Technical Requirements

**Architecture:** Pipeline monorepo. Data plane = TigerGraph Savanna (graph + vector). Control plane = Python orchestrator invoking pipeline modules. All three pipelines share the same retrieval primitives; only their composition differs.

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Static HTML dashboard (Vite build → `docs/`) | Zero infra, judge-friendly |
| Backend | Python 3.11 + FastAPI (thin, for demo endpoint) | Standard, fast to demo |
| Graph DB | TigerGraph Savanna | Required by hackathon; free credits provided |
| Vector DB | TigerGraph Vector Index | Native, keeps everything in one place |
| Embeddings | `text-embedding-3-small` (OpenAI) or `bge-small-en-v1.5` local fallback | Cheap, good enough for 5.5M tokens |
| LLM | Claude Sonnet 4.5 primary; GPT-4o-mini for cheap sub-agents | Best reasoning for orchestrator; cost-tuned tools |
| Agent framework | Custom loop (no LangGraph) | Full control of state, budget, traces |
| MCP | TigerGraph MCP for dev-time graph inspection | Judged bonus |
| Ingest | Python + `mwparserfromhell` for infobox parsing | Deterministic first, LLM fallback |
| Infra | Local dev + Docker; Savanna hosted | Reproducible |

**Non-functional requirements:**
- **Performance:** ≤ 20 s median latency for agentic; ≤ 5 s for RAG; parallel bench across ≥ 8 workers.
- **Security:** API keys via `.env` only, never committed; input validation on demo endpoint; prompt-injection guard on retrieved passages.
- **Reliability:** Every tool call retried with backoff; hard step cap (8) and token budget (30k) per agentic run; graceful degradation to GraphRAG if agent exceeds budget.
- **Privacy / compliance:** Corpus is CC BY-SA 4.0 Wikipedia — attribution preserved in output.
- **Cost:** ≤ $50 total LLM spend for full 150-question benchmark on the agentic pipeline.
- **Maintainability:** `README.md`, `Makefile`, typed Python (mypy), pytest for tools + scorers.

---

## 🏗️ 7. MVP Scope (Must-Haves)

- [ ] Corpus loaded into Savanna: `Document`, `Chunk`, `Entity`, `Games`, `Event`, `Venue`, `Nation`, `Person` with `MENTIONS`, `PART_OF`, `HELD_AT`, `WON`, `COMPETED_IN` edges.
- [ ] RAG pipeline returns cited answers on `eval_public`.
- [ ] GraphRAG pipeline uses entity-linked subgraph + vector hits.
- [ ] Agentic orchestrator with tools: `entity_link`, `graph_hop`, `pattern_match`, `vector_search`, `doc_fetch`, `aggregate`, `evaluate_evidence`, `answer`.
- [ ] Bench harness scores exact-match accuracy, recall@K vs `gold_doc_ids`, tokens, latency — sliced by `qtype`.
- [ ] Static HTML dashboard published to `docs/index.html`.
- [ ] Predictions on `eval_hidden.jsonl` from the agentic pipeline.
- [ ] Architecture diagram + 3–5 min demo video + README with reproducible setup.

---

## 🛑 8. Out of Scope (Not Now)

🚫 Fine-tuning any model.
🚫 Non-Wikipedia corpora / open-web retrieval.
🚫 Multi-user auth or hosted UI beyond the static dashboard.
🚫 Round-2 temporal reasoning implementation (only schema hooks land in Round 1).
🚫 Mobile app / browser extension.
🚫 Realtime streaming responses.

---

## 📊 9. Success Criteria

| Metric Category | Measurable Target | Desired Outcome |
|---|---|---|
| Product Metric | All 3 pipelines answer all 100 public questions with citations | Benchmark is complete |
| Model Metric — accuracy | Agentic ≥ 70% overall; ≥ 60% multi_hop; ≥ 65% aggregation | Beats baseline decisively |
| Model Metric — retrieval | Recall@K vs `gold_doc_ids` ≥ 0.85 (agentic) | Right evidence is being pulled |
| Model Metric — efficiency | Median ≤ 15k tokens / question (agentic) | Efficient, not brute-forced |
| Reliability | 0 uncaught exceptions on full bench run | Reproducible for judges |
| Business / Academic | Top 15 finish in Round 1 → Round 2 invite | Advance to finals |

---

## 🗓️ 10. Milestones

| Phase | Deliverable | Target date |
|---|---|---|
| Research and design | This PRD, schema draft, architecture diagram | 29 Sept |
| Ingest + baseline | Corpus in Savanna, embeddings live, RAG working | 29 Sept EOD |
| GraphRAG + entity linker | Infobox extraction, subgraph retrieval, cited answers | 30 Sept AM |
| Agentic orchestrator | Tools + loop + per-qtype routing, first bench pass | 30 Sept midday |
| Bench + dashboard + video | All three pipelines scored, dashboard shipped, demo recorded | 30 Sept EOD |
| Round 1 submission | GitHub repo public, submission form filled | 30 Sept, before 23:59 |
| Round 2 (if selected) | Temporal-conflict logic, harder dataset run, write-up | 1–7 Oct |

---

## ⚠️ 11. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Savanna free credits exhausted during dev | Med | High | Local DuckDB + FAISS mirror for iteration; Savanna only for scored runs |
| LLM cost overrun on 150 Qs × 3 pipelines | Med | High | Hard token budget per run; GPT-4o-mini for sub-agents; cache all LLM calls by hash |
| Infobox parsing gaps → wrong aggregation counts | High | High | LLM extraction fallback + reconcile against vector-retrieved passages; unit tests on gold set |
| Entity-linking fails on ambiguous names ("Chen") | High | Med | Build alias index from Wikipedia redirects; require QID confirmation via `wikidata_qid` field before graph_hop |
| Agent loops burning tokens without converging | Med | High | Step cap (8), mandatory `evaluate_evidence` gate, fallback to GraphRAG answer on budget exhaustion |
| Tight 24-hr deadline before Round 1 | High | High | Freeze scope at MVP list above; buffer built into 30 Sept afternoon |
| Prompt injection via retrieved passages | Low | Med | Wrap retrieved text in `<untrusted>` tags; instruct LLM to treat as data only |

---

## ❓ 12. Open Questions and Assumptions

**Assumptions**
- [ ] Savanna free-tier credits cover ~5.5M tokens of embeddings + ~150 benchmark runs.
- [ ] `text-embedding-3-small` is sufficient for Olympics-domain retrieval — no domain-specific embedding model needed.
- [ ] The 100 public questions are representative of the 50 hidden ones (same distribution across qtypes).
- [ ] LLM-as-judge scoring in the hackathon accepts exact-match + normalized string comparison for aggregation answers.

**Open Questions**
- Q1: Does Savanna's vector index support metadata filters natively, or do we filter post-retrieval?
- Q2: What's the token-cost cap the judges consider "efficient"? (Assume 15k median until stated.)
- Q3: For Round 2, is the "harder dataset" additive on the same corpus or a separate one?
- Q4: Can we use Claude Sonnet 4.5 (bring-your-own key) or is there a mandated model?

---

## ✅ 13. Definition of Done

- [ ] All MVP items pass acceptance criteria in section 5
- [ ] Public GitHub repo with README, `Makefile`, and one-command bench run
- [ ] pytest suite green on tools + scorers
- [ ] No API keys or `.env` in the repo; `.env.example` provided
- [ ] Architecture diagram (PNG + editable source) in `docs/`
- [ ] Demo video (3–5 min) linked in README
- [ ] `results/` folder committed with per-pipeline scores + `eval_hidden` predictions
- [ ] Metrics dashboard rendered at `docs/index.html`, viewable via GitHub Pages
- [ ] Submission form on Unstop completed before 30 Sept 23:59 IST

---

## 📎 14. References

- Hackathon brief: [abt_hackathon.md](abt_hackathon.md)
- Corpus + questions: [hackathon-resources/](hackathon-resources-20260929T113614Z-1-001/hackathon-resources/)
- Guidebook: https://alluring-beryllium-491.notion.site/Agentic-GraphRAG-Hackathon-Guidebook-34fc2cb129c08146998af3568d7d2594
- Dataset drive: https://drive.google.com/drive/folders/10C0hzRaHlm00VYPFbjapKtWj0EPmLvQ9
- Discord: https://discord.gg/eKWm3mbkw2
- TigerGraph Savanna docs — TBD link
- TigerGraph MCP — TBD link
- Microsoft GraphRAG reference — https://microsoft.github.io/graphrag/
