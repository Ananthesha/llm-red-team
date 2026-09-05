# Phase 2 — Adapters & Attack Generator  [DONE]

## Goal
Define the single seam to any target app, and the agentic step that expands seeds
into varied adversarial test cases.

## Files
- `redteam/adapters/base.py` — `TargetAdapter` protocol: `send(prompt) -> str`, `name`
- `redteam/adapters/function_adapter.py` — wrap any Python callable
- `redteam/adapters/http_adapter.py` — POST to a REST endpoint; dotted `response_path` extraction (this is where the AI interview site plugs in later)
- `redteam/adapters/__init__.py` — `build_target("sample")` registry
- `redteam/generator.py` — `TestCase`, `expand_seed()`, `generate_suite()`; asks Claude for N variants per seed, falls back to the seed prompt if generation fails

## Design notes
- Generator is best-effort: a seed always yields at least itself (`<seed>-0`), plus up to N variants (`<seed>-1..N`).
- Variants stay in-category; system prompt frames this as defensive testing of an app you control.

## Done when
- Adapters satisfy the protocol; generator produces test cases (live variants need API key, offline still yields the seed itself).

## Verify
```
python3 -m pytest tests/test_adapters.py -q
```
Status: verified — adapter tests pass. Live variant generation exercised in Phase 6.
