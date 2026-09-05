import pytest

from redteam.adapters import FunctionAdapter, HTTPAdapter, TargetAdapter


def test_function_adapter_roundtrip():
    a = FunctionAdapter(lambda p: f"echo:{p}", name="echo")
    assert isinstance(a, TargetAdapter)
    assert a.send("hi") == "echo:hi"
    assert a.name == "echo"


def test_http_adapter_extracts_nested_path():
    a = HTTPAdapter("http://x", response_path="choices.0.message.content")
    data = {"choices": [{"message": {"content": "hello"}}]}
    assert a._extract(data) == "hello"


def test_http_adapter_bad_path_raises():
    a = HTTPAdapter("http://x", response_path="a.b")
    with pytest.raises((KeyError, ValueError)):
        a._extract({"a": "not-a-dict"})
