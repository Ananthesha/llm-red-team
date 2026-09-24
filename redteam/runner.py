"""Runner: fire each test case at the target adapter and record the response.

Kept deliberately simple - sequential with basic retry/backoff. Results are written
as JSONL so a run can be inspected, re-judged, or diffed later without re-hitting the
target.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass

from .adapters.base import TargetAdapter
from .generator import TestCase


@dataclass
class RunResult:
    """One test case executed against the target."""

    id: str
    category: str
    prompt: str
    derived_from: str
    response: str
    latency_s: float
    error: str = ""


def _send_with_retry(target: TargetAdapter, prompt: str, retries: int, backoff: float):
    """Call target.send with retries; return (response, latency, error)."""
    last_err = ""
    for attempt in range(retries + 1):
        start = time.time()
        try:
            resp = target.send(prompt)
            return resp, time.time() - start, ""
        except Exception as exc:  # noqa: BLE001 - we record and continue
            last_err = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(backoff * (2**attempt))
    return "", 0.0, last_err


def run_suite(
    target: TargetAdapter,
    cases: list[TestCase],
    *,
    retries: int = 2,
    backoff: float = 1.0,
    progress: bool = True,
    isolate: bool = True,
) -> list[RunResult]:
    """Execute every test case and return results (including any that errored).

    `isolate` calls the target's optional `reset()` before each case, so stateful
    targets (e.g. InterviewIQTarget, which holds an interview session) start each
    test case clean. Without it, an early attack that derails the app's persona
    contaminates every later verdict. Stateless targets have no `reset()` and are
    unaffected.
    """
    results: list[RunResult] = []
    total = len(cases)
    reset = getattr(target, "reset", None) if isolate else None
    for i, case in enumerate(cases, start=1):
        if reset is not None:
            reset()
        response, latency, error = _send_with_retry(target, case.prompt, retries, backoff)
        results.append(
            RunResult(
                id=case.id,
                category=case.category,
                prompt=case.prompt,
                derived_from=case.derived_from,
                response=response,
                latency_s=round(latency, 3),
                error=error,
            )
        )
        if progress:
            status = "ERR" if error else "ok"
            print(f"[{i}/{total}] {case.id} ({case.category}) -> {status}")
    return results


def results_to_jsonl(results: list[RunResult]) -> str:
    return "\n".join(json.dumps(asdict(r)) for r in results)


def load_results(path: str) -> list[RunResult]:
    """Load results back from a JSONL file."""
    out: list[RunResult] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(RunResult(**json.loads(line)))
    return out
