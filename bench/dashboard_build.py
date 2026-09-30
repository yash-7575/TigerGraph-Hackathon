"""Build docs/index.html from per-pipeline summary.csv files."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from core.config import ROOT


PIPELINES = ["rag", "graphrag", "agentic"]


HTML_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Agentic GraphRAG — Benchmark</title>
<style>
  body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:2rem;background:#0d1117;color:#e6edf3;}}
  h1{{margin:.2rem 0;font-size:1.6rem;}} h2{{margin-top:2.2rem;color:#79c0ff;}}
  .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1rem;}}
  .card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;}}
  .card h3{{margin:0 0 .5rem;font-size:1rem;color:#7ee787;}}
  .metric{{font-size:1.5rem;font-weight:600;margin:.2rem 0;}}
  table{{border-collapse:collapse;margin-top:.8rem;width:100%;font-size:.9rem;}}
  th,td{{border:1px solid #30363d;padding:.35rem .6rem;text-align:left;}}
  th{{background:#21262d;}}
  .bar{{background:#238636;height:8px;border-radius:4px;}}
  .pill{{display:inline-block;background:#1f6feb;color:white;padding:.15rem .5rem;border-radius:12px;font-size:.75rem;}}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
</head>
<body>
<h1>Agentic GraphRAG — Three-Pipeline Benchmark</h1>
<p>TigerGraph Hackathon · corpus: 2,951 Wikipedia docs · eval: 100 public questions</p>

<h2>Headline</h2>
<div class="grid">{cards}</div>

<h2>Accuracy by question type</h2>
<canvas id="acc" height="120"></canvas>

<h2>Cost & latency (median per question)</h2>
<canvas id="cost" height="120"></canvas>

<h2>Per-pipeline detail</h2>
{tables}

<h2>Sample questions</h2>
{samples}

<script>
const perQtype = {per_qtype_json};
const summary = {summary_json};

const qtypes = [...new Set(Object.values(perQtype).flat().map(r=>r.qtype))].sort();

function series(field){{
  return Object.entries(perQtype).map(([p,rows])=>({{
    label: p,
    data: qtypes.map(qt => {{
      const r = rows.find(x=>x.qtype===qt);
      return r ? (r[field]??0) : 0;
    }}),
    borderWidth: 1,
  }}));
}}

new Chart(document.getElementById('acc'), {{
  type: 'bar',
  data: {{labels: qtypes, datasets: series('accuracy')}},
  options: {{scales: {{y: {{min:0,max:1}}}}, plugins:{{legend:{{labels:{{color:'#e6edf3'}}}}}}}}
}});

new Chart(document.getElementById('cost'), {{
  type: 'bar',
  data: {{labels: qtypes, datasets: series('tokens_in')}},
  options: {{plugins:{{legend:{{labels:{{color:'#e6edf3'}}}}}}}}
}});
</script>
</body></html>
"""


def _card(pipeline: str, df: pd.DataFrame) -> str:
    n = len(df)
    correct = df["correct"].mean() if df["correct"].notna().any() else 0.0
    tok = int(df["tokens_in"].median() + df["tokens_out"].median())
    lat = int(df["latency_ms"].median())
    return (
        f'<div class="card"><h3>{pipeline.upper()}</h3>'
        f'<div class="metric">{correct * 100:.1f}%</div>'
        f'<div>accuracy on {n} Qs</div>'
        f'<div style="margin-top:.6rem;font-size:.85rem;color:#8b949e;">'
        f'{tok} med tokens · {lat/1000:.1f}s median</div></div>'
    )


def _table(pipeline: str, per: list[dict]) -> str:
    rows = "".join(
        f"<tr><td>{r['qtype']}</td><td>{r['n']}</td>"
        f"<td>{(r.get('accuracy') or 0) * 100:.1f}%</td>"
        f"<td>{(r.get('recall') or 0) * 100:.1f}%</td>"
        f"<td>{int(r.get('tokens_in') or 0)}</td>"
        f"<td>{int((r.get('latency_ms') or 0))/1000:.1f}s</td></tr>"
        for r in per
    )
    return (
        f'<h3><span class="pill">{pipeline}</span></h3>'
        f'<table><thead><tr><th>qtype</th><th>n</th><th>accuracy</th>'
        f'<th>recall</th><th>med tokens</th><th>med latency</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


def _samples(dfs: dict[str, pd.DataFrame]) -> str:
    if not dfs:
        return ""
    ref = next(iter(dfs.values()))
    sample_qids = ref["qid"].head(5).tolist()
    out = "<table><thead><tr><th>qid</th><th>qtype</th><th>gold</th>"
    for p in dfs: out += f"<th>{p}</th>"
    out += "</tr></thead><tbody>"
    for qid in sample_qids:
        row = "<tr>"
        r0 = ref[ref["qid"] == qid].iloc[0]
        row += f"<td>{qid}</td><td>{r0['qtype']}</td><td>{r0['gold_answer']}</td>"
        for p, df in dfs.items():
            m = df[df["qid"] == qid]
            if len(m):
                a = str(m.iloc[0]["answer"])[:80]
                ok = "✓" if m.iloc[0]["correct"] else "✗"
                row += f"<td>{ok} {a}</td>"
            else:
                row += "<td>-</td>"
        row += "</tr>"
        out += row
    out += "</tbody></table>"
    return out


def build() -> None:
    dfs: dict[str, pd.DataFrame] = {}
    per: dict[str, list[dict]] = {}
    for p in PIPELINES:
        sp = ROOT / "results" / p / "summary.csv"
        pp = ROOT / "results" / p / "per_qtype.json"
        if sp.exists():
            dfs[p] = pd.read_csv(sp)
        if pp.exists():
            per[p] = json.loads(pp.read_text())

    cards = "\n".join(_card(p, df) for p, df in dfs.items()) or "<div>No results yet.</div>"
    tables = "\n".join(_table(p, per.get(p, [])) for p in dfs)
    samples = _samples(dfs)

    html = HTML_TEMPLATE.format(
        cards=cards,
        tables=tables,
        samples=samples,
        per_qtype_json=json.dumps(per),
        summary_json=json.dumps({p: len(df) for p, df in dfs.items()}),
    )
    out = ROOT / "docs" / "index.html"
    out.write_text(html)
    print(f"wrote {out}")


if __name__ == "__main__":
    build()
