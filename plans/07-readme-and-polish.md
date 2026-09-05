# Phase 7 — README & Polish  [NOT STARTED]

## Goal
Make the repo resume-credible: a README an interviewer respects, and a clean repo.

## Files to create
- `README.md` — problem statement; why LLM red-teaming matters; the 6-category taxonomy with rationale; architecture (taxonomy -> generator -> runner -> judge -> report); **judge calibration accuracy** (the credibility anchor); sample findings; limitations; ethics note (defensive testing of a target you control); the pluggable-adapter note (future: wire in the AI interview site)
- `.gitignore` — venv, `__pycache__`, `*.jsonl` run outputs (but keep `data/calibration_set.jsonl`), local `report.html`
- `reports/sample_report.html` — committed example (from Phase 5/6)
- optional: architecture diagram (mermaid in the README)

## Done when
- README reads well top to bottom and explains the calibration number.
- Repo has no stray artifacts; `pytest` green; sample report committed.

## Verify
- Fresh clone -> `pip install -e ".[dev]"` -> `pytest` passes.
- Open `reports/sample_report.html` — renders correctly.
- README skim: a reviewer understands what it does and why it's credible in <2 min.

## Interview talking points to bake in
- "Judge agrees with human labels X% of the time (n=23)."
- "Adding a hardened system prompt raised the safe rate from A% to B%."
- "Rule layer catches high-confidence leaks with ~zero false positives; LLM judge handles the nuanced rest."
