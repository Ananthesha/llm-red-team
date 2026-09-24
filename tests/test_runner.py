from redteam.generator import TestCase as _TestCase  # aliased: pytest tries to collect "Test*"
from redteam.runner import run_suite


class StatefulTarget:
    """Records the order of reset/send calls, like a session-holding adapter."""

    name = "stateful"

    def __init__(self):
        self.calls: list[str] = []

    def reset(self) -> None:
        self.calls.append("reset")

    def send(self, prompt: str) -> str:
        self.calls.append(f"send:{prompt}")
        return f"reply to {prompt}"


class StatelessTarget:
    name = "stateless"

    def send(self, prompt: str) -> str:
        return f"reply to {prompt}"


def _cases(n: int) -> list[_TestCase]:
    return [
        _TestCase(id=f"c{i}", category="jailbreak", prompt=f"p{i}", derived_from=f"s{i}")
        for i in range(n)
    ]


def test_isolate_resets_before_every_case():
    target = StatefulTarget()
    run_suite(target, _cases(2), progress=False)
    assert target.calls == ["reset", "send:p0", "reset", "send:p1"]


def test_no_isolate_keeps_one_session():
    target = StatefulTarget()
    run_suite(target, _cases(2), progress=False, isolate=False)
    assert target.calls == ["send:p0", "send:p1"]


def test_stateless_target_without_reset_still_runs():
    results = run_suite(StatelessTarget(), _cases(2), progress=False)
    assert [r.response for r in results] == ["reply to p0", "reply to p1"]
    assert all(r.error == "" for r in results)
