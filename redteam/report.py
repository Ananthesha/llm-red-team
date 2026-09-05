"""Report: judge a run's results and render a self-contained HTML vulnerability report.

The report shows the headline safety score, the judge's calibration accuracy (so the
reader knows how much to trust the numbers), a per-category breakdown, and a
severity-ranked list of the failing cases with prompt / response / rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .calibration import CalibrationReport
from .judge import judge_response
from .runner import RunResult
from .taxonomy import CATEGORY_INFO, SEVERITY_ORDER, Category

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


@dataclass
class JudgedResult:
    result: RunResult
    verdict: str
    rationale: str
    source: str
    severity: str


def judge_results(results: list[RunResult], progress: bool = True) -> list[JudgedResult]:
    """Run the judge over every result."""
    judged: list[JudgedResult] = []
    total = len(results)
    for i, r in enumerate(results, start=1):
        v = judge_response(r.category, r.prompt, r.response)
        judged.append(
            JudgedResult(
                result=r,
                verdict=v.verdict,
                rationale=v.rationale,
                source=v.source,
                severity=CATEGORY_INFO[Category(r.category)]["severity"],
            )
        )
        if progress:
            print(f"[judge {i}/{total}] {r.id} -> {v.verdict}")
    return judged


def _summarise(judged: list[JudgedResult]) -> dict:
    """Compute headline stats and per-category breakdown."""
    total = len(judged)
    counts = {"vulnerable": 0, "partial": 0, "safe": 0}
    per_cat: dict[str, dict] = {}

    for j in judged:
        counts[j.verdict] += 1
        cat = per_cat.setdefault(
            j.result.category,
            {
                "title": CATEGORY_INFO[Category(j.result.category)]["title"],
                "severity": j.severity,
                "vulnerable": 0,
                "partial": 0,
                "safe": 0,
                "total": 0,
            },
        )
        cat[j.verdict] += 1
        cat["total"] += 1

    for cat in per_cat.values():
        cat["safe_rate"] = round(100 * cat["safe"] / cat["total"]) if cat["total"] else 0

    safe_rate = round(100 * counts["safe"] / total) if total else 0
    # Severity-ranked failing cases (vulnerable first, then partial), critical first.
    failing = [j for j in judged if j.verdict in ("vulnerable", "partial")]
    failing.sort(
        key=lambda j: (
            0 if j.verdict == "vulnerable" else 1,
            SEVERITY_ORDER.get(j.severity, 9),
        )
    )
    ordered_cats = sorted(
        per_cat.values(), key=lambda c: SEVERITY_ORDER.get(c["severity"], 9)
    )
    return {
        "total": total,
        "counts": counts,
        "safe_rate": safe_rate,
        "per_category": ordered_cats,
        "failing": failing,
    }


def render_report(
    judged: list[JudgedResult],
    *,
    target_name: str,
    calibration: CalibrationReport | None = None,
) -> str:
    """Render the HTML report string."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html.j2")
    summary = _summarise(judged)
    return template.render(
        target_name=target_name,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        summary=summary,
        calibration=calibration,
    )
