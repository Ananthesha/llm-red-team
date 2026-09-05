"""Target adapters and a small registry for the CLI's --target flag."""

from __future__ import annotations

from .base import TargetAdapter
from .function_adapter import FunctionAdapter
from .http_adapter import HTTPAdapter
from .sample_target import SampleTarget


def build_target(name: str) -> TargetAdapter:
    """Construct a built-in target by name for the CLI.

    Only the demo `sample` target is buildable without extra config; HTTP and
    function adapters are constructed programmatically by callers who supply the
    endpoint or callable.
    """
    if name == "sample":
        return SampleTarget()
    raise ValueError(
        f"Unknown built-in target '{name}'. Available: sample. "
        "For a REST endpoint or Python callable, use HTTPAdapter / FunctionAdapter directly."
    )


__all__ = [
    "TargetAdapter",
    "FunctionAdapter",
    "HTTPAdapter",
    "SampleTarget",
    "build_target",
]
