"""Calibration: measure how well the judge agrees with human labels.

Reads data/calibration_set.jsonl - hand-labeled (category, prompt, response,
true_verdict) rows - runs the judge over each, and reports accuracy plus a 3x3
confusion matrix. The reported accuracy is the credibility anchor for the whole
eval: it tells an interviewer how much to trust the automated verdicts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .judge import VERDICTS, Verdict, judge_response

CALIBRATION_PATH = Path(__file__).resolve().parent.parent / "data" / "calibration_set.jsonl"


@dataclass
class CalibrationItem:
    category: str
    prompt: str
    response: str
    true_verdict: str


@dataclass
class CalibrationReport:
    n: int
    accuracy: float
    confusion: dict[str, dict[str, int]]  # true -> predicted -> count
    items: list[tuple[CalibrationItem, Verdict]]

    def confusion_text(self) -> str:
        header = "true\\pred".ljust(12) + "".join(v.ljust(12) for v in VERDICTS)
        lines = [header]
        for t in VERDICTS:
            row = t.ljust(12) + "".join(str(self.confusion[t][p]).ljust(12) for p in VERDICTS)
            lines.append(row)
        return "\n".join(lines)


def load_calibration_set(path: Path | None = None) -> list[CalibrationItem]:
    p = path or CALIBRATION_PATH
    items: list[CalibrationItem] = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            items.append(
                CalibrationItem(
                    category=row["category"],
                    prompt=row["prompt"],
                    response=row["response"],
                    true_verdict=row["true_verdict"],
                )
            )
    return items


def run_calibration(path: Path | None = None) -> CalibrationReport:
    items = load_calibration_set(path)
    confusion = {t: {p: 0 for p in VERDICTS} for t in VERDICTS}
    correct = 0
    judged: list[tuple[CalibrationItem, Verdict]] = []

    for item in items:
        verdict = judge_response(item.category, item.prompt, item.response)
        judged.append((item, verdict))
        if item.true_verdict in confusion and verdict.verdict in confusion[item.true_verdict]:
            confusion[item.true_verdict][verdict.verdict] += 1
        if verdict.verdict == item.true_verdict:
            correct += 1

    n = len(items)
    accuracy = correct / n if n else 0.0
    return CalibrationReport(n=n, accuracy=accuracy, confusion=confusion, items=judged)
