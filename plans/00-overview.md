# LLM Red-Team / Eval Toolkit — Plan Index

This folder splits the master plan into one file per phase so you can implement (or
re-run) them one at a time. Each file is self-contained: goal, files it touches,
what "done" looks like, and how to verify.

**Master plan:** `~/.claude/plans/ok-i-wanna-go-toasty-sunset.md`

## Status legend
- [x] done and verified
- [~] partially done
- [ ] not started

## Phases

| # | File | Topic | Status |
|---|------|-------|--------|
| 1 | `01-scaffold-and-taxonomy.md` | Repo scaffold, attack taxonomy, 60 seed prompts, sample target | [x] |
| 2 | `02-generator-and-adapters.md` | Adapter protocol + function/http/sample; attack generator | [x] |
| 3 | `03-runner.md` | Execution engine, retries, results JSONL | [x] |
| 4 | `04-judge-and-calibration.md` | Rule + LLM judge; hand-labeled calibration set; accuracy score | [x] |
| 5 | `05-report.md` | HTML report (safe rate, per-category, ranked findings) | [x] |
| 6 | `06-cli-and-live-run.md` | CLI wiring [x] + first live run (needs API key) [ ] | [~] |
| 7 | `07-readme-and-polish.md` | README, sample report artifact, ethics note, repo polish | [x] |

## How to drive this
Prompt me with, e.g., "implement plan 05" or "do phase 6" and I'll open that file
and execute just that phase. Phases 1-4 are already built and tested; 5-6 are
partially done (code exists; the live run and committed sample report still need
your ANTHROPIC_API_KEY); 7 is the write-up.

## What still needs YOU
- Export `ANTHROPIC_API_KEY` so the live commands (`run`, `report`, `calibrate`,
  `regress`) can actually call Claude. Everything else runs offline.
