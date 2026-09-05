# Phase 4 — Judge & Calibration  [DONE]

## Goal
Score each response vulnerable/partial/safe, and prove how much to trust the judge
by measuring it against hand labels. This is the credibility centerpiece.

## Files
- `redteam/judge.py` — rule-based checks (system-prompt canary, secret/PII regex) that win when they fire; LLM judge with per-category rubric; `judge_response()`
- `redteam/calibration.py` — `run_calibration()`, accuracy + 3x3 confusion matrix
- `data/calibration_set.jsonl` — 23 hand-labeled (category, prompt, response, true_verdict) rows across all categories and all three verdicts

## Design notes
- Rule layer first (near-zero false positives), LLM judge for the rest.
- Empty response -> safe. Malformed judge output -> keyword recovery, then default partial.

## Done when
- Rule verdicts deterministic; LLM path mockable; calibration reports an accuracy %.

## Verify
```
python3 -m pytest tests/test_judge.py -q          # offline, mocks the LLM
python3 -m redteam.cli calibrate                  # LIVE: needs ANTHROPIC_API_KEY
```
Status: judge unit tests pass (5/5). Live `calibrate` run pending API key (Phase 6).
Target: report whatever accuracy comes out honestly (>70% is a good sign).
