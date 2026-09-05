"""The TargetAdapter protocol: the single seam between the toolkit and any app
under test.

Every target - the sample demo, a REST endpoint, or (later) the AI interview site -
implements `send(prompt) -> str`. Nothing else in the toolkit knows how the target
works, so adding a new target is one new adapter and zero core changes.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TargetAdapter(Protocol):
    """Anything that can take an attacker prompt and return the app's reply."""

    #: Short label used in reports (e.g. "sample", "interview-site").
    name: str

    def send(self, prompt: str) -> str:
        """Send one prompt to the target app and return its text response."""
        ...
