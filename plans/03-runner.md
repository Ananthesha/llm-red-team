# Phase 3 — Runner  [DONE]

## Goal
Execute a suite of test cases against a target and persist results so they can be
re-judged or diffed without re-hitting the target.

## Files
- `redteam/runner.py` — `RunResult`, `run_suite()` (sequential, retry+backoff), `results_to_jsonl()`, `load_results()`

## Design notes
- Errors are recorded per case (never abort the whole run).
- Results written as JSONL: id, category, prompt, derived_from, response, latency_s, error.

## Done when
- `run_suite()` produces one `RunResult` per case and round-trips through JSONL.

## Verify
Live run in Phase 6. Offline, the dataclass round-trip is covered indirectly by the
report test which constructs `RunResult`s directly.
Status: code complete; end-to-end exercised in Phase 6.
