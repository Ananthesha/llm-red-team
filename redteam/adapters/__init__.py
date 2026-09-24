"""Target adapters and a small registry for the CLI's --target flag."""

from __future__ import annotations

import os

from .base import TargetAdapter
from .function_adapter import FunctionAdapter
from .http_adapter import HTTPAdapter
from .interview_iq import InterviewIQTarget
from .sample_target import SampleTarget


def build_target(name: str) -> TargetAdapter:
    """Construct a built-in target by name for the CLI.

    `sample` and `interview-iq` are buildable without extra config (interview-iq
    reads its base URL and test-account credentials from environment variables,
    falling back to local-dev defaults). HTTP and function adapters for arbitrary
    endpoints are constructed programmatically by callers who supply the
    endpoint or callable.
    """
    if name == "sample":
        return SampleTarget()
    if name == "interview-iq":
        return InterviewIQTarget(
            base_url=os.environ.get("INTERVIEWIQ_BASE_URL", "http://localhost:5000"),
            email=os.environ.get("INTERVIEWIQ_EMAIL", "eval-harness@example.com"),
            password=os.environ.get("INTERVIEWIQ_PASSWORD", "password123"),
        )
    raise ValueError(
        f"Unknown built-in target '{name}'. Available: sample, interview-iq. "
        "For a REST endpoint or Python callable, use HTTPAdapter / FunctionAdapter directly."
    )


__all__ = [
    "TargetAdapter",
    "FunctionAdapter",
    "HTTPAdapter",
    "InterviewIQTarget",
    "SampleTarget",
    "build_target",
]
