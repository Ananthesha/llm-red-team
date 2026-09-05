"""Command-line entry point.

Commands:
  redteam run       generate + execute a suite against a target, write results JSONL
  redteam calibrate score the judge against the hand-labeled calibration set
  redteam report    judge a results file and render an HTML report
  redteam regress   re-run against a (possibly hardened) target and diff vs a baseline
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .adapters import build_target
from .adapters.sample_target import SampleTarget


def _cmd_run(args: argparse.Namespace) -> int:
    from .generator import generate_suite, testcases_to_jsonl
    from .runner import results_to_jsonl, run_suite

    target = build_target(args.target)
    print(f"Generating suite ({args.variants} variants/seed)...")
    cases = generate_suite(variants_per_seed=args.variants)
    print(f"  {len(cases)} test cases.")
    if args.cases_out:
        Path(args.cases_out).write_text(testcases_to_jsonl(cases))
    print(f"Running against target '{target.name}'...")
    results = run_suite(target, cases)
    Path(args.out).write_text(results_to_jsonl(results))
    errs = sum(1 for r in results if r.error)
    print(f"Wrote {len(results)} results to {args.out} ({errs} errors).")
    return 0


def _cmd_calibrate(args: argparse.Namespace) -> int:
    from .calibration import run_calibration

    print("Scoring judge against calibration set...")
    report = run_calibration()
    print(f"\nJudge accuracy: {report.accuracy * 100:.1f}%  (n={report.n})\n")
    print(report.confusion_text())
    if args.verbose:
        print("\nDisagreements:")
        for item, verdict in report.items:
            if verdict.verdict != item.true_verdict:
                print(f"  [{item.category}] true={item.true_verdict} pred={verdict.verdict}"
                      f" :: {verdict.rationale}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    from .calibration import run_calibration
    from .report import judge_results, render_report
    from .runner import load_results

    results = load_results(args.results)
    print(f"Judging {len(results)} results...")
    judged = judge_results(results)
    calibration = None
    if not args.no_calibration:
        print("Computing judge calibration for the report header...")
        calibration = run_calibration()
    html = render_report(judged, target_name=args.target_name, calibration=calibration)
    Path(args.out).write_text(html)
    print(f"Wrote report to {args.out}")
    return 0


def _cmd_regress(args: argparse.Namespace) -> int:
    """Re-run the same suite against a hardened target and diff safe rates."""
    from .generator import generate_suite
    from .report import judge_results
    from .runner import load_results, results_to_jsonl, run_suite

    baseline = load_results(args.baseline)
    print(f"Loaded baseline: {len(baseline)} results.")
    # Reuse the exact baseline prompts so the comparison is apples-to-apples.
    from .generator import TestCase

    cases = [
        TestCase(id=r.id, category=r.category, prompt=r.prompt, derived_from=r.derived_from)
        for r in baseline
    ]
    target = SampleTarget(hardened=True) if args.target == "sample" else build_target(args.target)
    print(f"Re-running {len(cases)} cases against '{target.name}'...")
    new_results = run_suite(target, cases)
    if args.out:
        Path(args.out).write_text(results_to_jsonl(new_results))

    base_rate = _safe_rate(judge_results(baseline, progress=False))
    new_rate = _safe_rate(judge_results(new_results, progress=False))
    print(f"\nBaseline safe rate: {base_rate}%")
    print(f"New safe rate:      {new_rate}%")
    print(f"Delta:             {new_rate - base_rate:+d} points")
    return 0


def _safe_rate(judged) -> int:
    total = len(judged)
    safe = sum(1 for j in judged if j.verdict == "safe")
    return round(100 * safe / total) if total else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="redteam", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="generate + execute a suite against a target")
    run.add_argument("--target", default="sample", help="built-in target name (default: sample)")
    run.add_argument("--variants", type=int, default=4, help="variants generated per seed")
    run.add_argument("--out", default="results.jsonl", help="results output path")
    run.add_argument("--cases-out", default="", help="optional path to save generated test cases")
    run.set_defaults(func=_cmd_run)

    cal = sub.add_parser("calibrate", help="score the judge against the calibration set")
    cal.add_argument("-v", "--verbose", action="store_true", help="print disagreements")
    cal.set_defaults(func=_cmd_calibrate)

    rep = sub.add_parser("report", help="judge results and render an HTML report")
    rep.add_argument("results", help="results JSONL from `redteam run`")
    rep.add_argument("--out", default="report.html", help="HTML output path")
    rep.add_argument("--target-name", default="sample", help="target label shown in the report")
    rep.add_argument("--no-calibration", action="store_true", help="skip judge calibration header")
    rep.set_defaults(func=_cmd_report)

    reg = sub.add_parser("regress", help="re-run vs a baseline and report the safe-rate delta")
    reg.add_argument("baseline", help="baseline results JSONL")
    reg.add_argument("--target", default="sample", help="target to re-run (sample -> hardened)")
    reg.add_argument("--out", default="", help="optional path to save the new results")
    reg.set_defaults(func=_cmd_regress)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 - top-level friendly error
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
