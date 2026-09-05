"""Adapter wrapping any local Python callable `str -> str`.

Useful for testing the toolkit and for targets that are importable Python code
rather than a network service.
"""

from __future__ import annotations

from typing import Callable


class FunctionAdapter:
    """Wrap a `prompt -> response` callable as a TargetAdapter."""

    def __init__(self, fn: Callable[[str], str], name: str = "function"):
        self._fn = fn
        self.name = name

    def send(self, prompt: str) -> str:
        return self._fn(prompt)
