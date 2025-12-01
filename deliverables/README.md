# Deliverables

Contents
- `inventory_clean.csv` – cleaned dataset.
- `anomalies.json` – issues flagged per row.
- `approach.md` – pipeline description.
- `cons.md` – limitations/tradeoffs.
- `prompts.md` – prompt log (note: deterministic pipeline, no live LLM calls).
- `run.py` – entry point to regenerate artifacts.
- `tests/` – regression coverage for key normalizers.
- (optional) `ddi_ideas.md` – future enrichment ideas.

How to run
- Regenerate outputs: `python3 run.py`
- Run tests: `python3 -m unittest discover -s tests`

Notes
- No external dependencies or network access are required; only Python 3.x from the standard library.
