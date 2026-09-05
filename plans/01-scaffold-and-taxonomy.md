# Phase 1 — Scaffold, Taxonomy & Seeds  [DONE]

## Goal
Stand up the Python package and define the attack taxonomy that every other module
reads from, plus 60 hand-written seed prompts and the demo "app under test."

## Files
- `pyproject.toml` — package metadata, deps (anthropic, jinja2, pyyaml, requests), `redteam` CLI entry point
- `redteam/__init__.py`
- `redteam/taxonomy.py` — `Category` enum (6), `CATEGORY_INFO` (title/description/failure/severity), `Seed`, `load_seeds()`
- `redteam/llm.py` — shared Anthropic client wrapper (`complete()`), API-key check
- `data/seeds/*.yaml` — 6 files x 10 seeds = 60 attack prompts
- `redteam/adapters/sample_target.py` — `SampleTarget` (InterviewCoach bot), base + hardened system prompts

## The 6 categories
jailbreak (high), prompt_injection (critical), system_prompt_extraction (high),
data_leakage (critical), off_topic_abuse (medium), hallucination_trap (medium)

## Done when
- `load_seeds()` returns 60 seeds, 10 per category, unique ids.

## Verify
```
python3 -c "from redteam.taxonomy import load_seeds; print(len(load_seeds()))"   # -> 60
```
Status: verified — prints 60.
