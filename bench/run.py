"""Run one or more pipelines against a question set and score them."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from loguru import logger
from tqdm import tqdm

from core.config import ROOT
from core.types import AnswerObject
from bench.scorers import any_hit, exact_match, recall_at_k


RESULTS = ROOT / "results"


def _load_questions(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _run_one(pipeline: str, q: dict) -> AnswerObject:
    qid = q["qid"]
    question = q["question"]
    qtype = q.get("qtype", "lookup")
    try:
        if pipeline == "rag":
            from pipelines.rag import answer
            return answer(question, qtype=qtype, qid=qid)
        elif pipeline == "graphrag":
            from pipelines.graphrag import answer  # noqa
            return answer(question, qtype=qtype, qid=qid)
        elif pipeline == "agentic":
            from pipelines.agentic.orchestrator import answer  # noqa
            return answer(question, qtype=qtype, qid=qid)
        else:
            raise ValueError(f"unknown pipeline: {pipeline}")
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[{pipeline}] {qid} failed: {e}")
        return AnswerObject(
            answer="", citations=[], pipeline=pipeline, qid=qid, error=f"{type(e).__name__}: {e}"
        )


def run_pipeline(pipeline: str, questions: list[dict], workers: int = 4) -> pd.DataFrame:
    out_dir = RESULTS / pipeline
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one, pipeline, q): q for q in questions}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=pipeline):
            q = futures[fut]
            ans: AnswerObject = fut.result()
            (out_dir / f"{q['qid']}.json").write_text(ans.model_dump_json(indent=2))

            gold = q.get("answer", [])
            gold_docs = q.get("gold_doc_ids", [])
            rows.append({
                "qid": q["qid"],
                "qtype": q.get("qtype", "lookup"),
                "correct": exact_match(ans.answer, gold) if gold else None,
                "any_hit": any_hit(ans.citations, gold_docs),
                "recall_at_k": recall_at_k(ans.citations, gold_docs),
                "n_citations": len(ans.citations),
                "tokens_in": ans.tokens.input,
                "tokens_out": ans.tokens.output,
                "cached": ans.tokens.cached,
                "latency_ms": ans.latency_ms,
                "budget_exceeded": ans.budget_exceeded,
                "error": ans.error,
                "answer": ans.answer,
                "gold_answer": gold[0] if gold else "",
            })

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "summary.csv", index=False)

    per = df.groupby("qtype").agg(
        n=("qid", "count"),
        accuracy=("correct", "mean"),
        recall=("recall_at_k", "mean"),
        tokens_in=("tokens_in", "median"),
        latency_ms=("latency_ms", "median"),
    ).reset_index()
    per.to_json(out_dir / "per_qtype.json", orient="records", indent=2)

    total_in = df["tokens_in"].sum()
    total_out = df["tokens_out"].sum()
    correct = df["correct"].mean() if df["correct"].notna().any() else None
    logger.info(f"[{pipeline}] accuracy={correct}, tokens_in={total_in}, tokens_out={total_out}")

    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", choices=["rag", "graphrag", "agentic", "all"], default="rag")
    ap.add_argument("--questions", default=str(ROOT / "data" / "eval_public.jsonl"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    qs = _load_questions(Path(args.questions))
    if args.limit:
        qs = qs[:args.limit]

    pipelines = ["rag", "graphrag", "agentic"] if args.pipeline == "all" else [args.pipeline]

    manifest = {
        "start_ts": time.time(),
        "questions": args.questions,
        "n_questions": len(qs),
        "pipelines": pipelines,
        "workers": args.workers,
    }
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        manifest["git_sha"] = git_sha
    except Exception:  # noqa: BLE001
        pass

    for p in pipelines:
        run_pipeline(p, qs, workers=args.workers)

    manifest["end_ts"] = time.time()
    (RESULTS / "run_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
