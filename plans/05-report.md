# Phase 5 — HTML Report  [PARTIAL]

## Goal
Turn a judged run into a self-contained, good-looking HTML vulnerability report.

## Files
- `redteam/report.py` — `judge_results()`, `_summarise()` (safe rate, per-category, severity-ranked findings), `render_report()`
- `redteam/templates/report.html.j2` — dark-theme template: stat cards, judge-accuracy card, per-category table with safe-rate bars, ranked finding cards (prompt / response / rationale)
- `reports/sample_report.html` — committed portfolio artifact  <-- STILL TO GENERATE

## Done when
- `render_report()` produces valid HTML with correct safe rate and finding blocks. [DONE]
- `reports/sample_report.html` exists in the repo as a viewable example. [PENDING]

## Verify
```
python3 -m pytest tests/test_report.py -q     # offline render test -> passes
```
To produce the committed sample artifact: either run the offline sample-generation
snippet, or (better) do a real `run` + `report` in Phase 6 and copy the output to
`reports/sample_report.html`.
Status: template + renderer done and tested. Committed sample HTML still to be
generated (blocked earlier; will regenerate).
