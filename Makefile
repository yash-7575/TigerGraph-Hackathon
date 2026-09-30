.PHONY: install ingest smoke rag graphrag agentic bench hidden dashboard test clean

PY := python3.12

install:
	$(PY) -m pip install --user --break-system-packages -r requirements.txt

smoke:
	$(PY) smoke_nvidia.py

ingest:
	$(PY) -m ingest.embedder

rag:
	$(PY) -m bench.run --pipeline rag --workers 4

graphrag:
	$(PY) -m bench.run --pipeline graphrag --workers 4

agentic:
	$(PY) -m bench.run --pipeline agentic --workers 2

bench:
	$(PY) -m bench.run --pipeline all --workers 2

hidden:
	$(PY) -m bench.run --pipeline agentic --questions data/eval_hidden.jsonl --workers 2

dashboard:
	$(PY) -m bench.dashboard_build

test:
	$(PY) -m pytest tests/ -v

clean:
	rm -rf .cache results/*/*.json results/*/summary.csv results/*/per_qtype.json
