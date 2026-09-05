# Phase 6 — CLI & First Live Run  [PARTIAL]

## Goal
One command-line tool that runs the whole pipeline, plus the first real end-to-end
run against the sample target.

## Files
- `redteam/cli.py` — subcommands: `run`, `calibrate`, `report`, `regress`

## Commands
```
redteam run --target sample --out results.jsonl        # generate + execute
redteam calibrate                                      # judge accuracy
redteam report results.jsonl --out report.html         # judge + render
redteam regress results.jsonl --out hardened.jsonl     # re-run hardened, diff safe rate
```

## Done when
- `--help` works offline. [DONE]
- A full live run produces results.jsonl -> report.html against the real Claude API. [PENDING - needs API key]
- Regression run shows the hardened system prompt improving the safe rate. [PENDING]

## Verify
```
export ANTHROPIC_API_KEY=sk-ant-...
python3 -m redteam.cli run --target sample --variants 3 --out results.jsonl
python3 -m redteam.cli report results.jsonl --out report.html --target-name "InterviewCoach"
python3 -m redteam.cli calibrate -v
python3 -m redteam.cli regress results.jsonl --out hardened.jsonl
```
Then open report.html in a browser and copy it to reports/sample_report.html.
Status: CLI complete and help verified offline. Live run is the main remaining
step and needs your API key — I cannot run it without one.
