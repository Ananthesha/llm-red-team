from unittest.mock import MagicMock, patch

from redteam.adapters import TargetAdapter
from redteam.adapters.interview_iq import InterviewIQTarget


def _resp(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


def test_is_target_adapter():
    assert isinstance(InterviewIQTarget(), TargetAdapter)


@patch("redteam.adapters.interview_iq.requests.post")
def test_login_success_skips_register(mock_post):
    mock_post.return_value = _resp(200, {"token": "tok-123"})
    target = InterviewIQTarget()

    headers = target._headers()

    assert headers == {"Authorization": "Bearer tok-123"}
    assert mock_post.call_count == 1
    assert mock_post.call_args.args[0].endswith("/api/auth/login")


@patch("redteam.adapters.interview_iq.requests.post")
def test_login_failure_falls_back_to_register(mock_post):
    mock_post.side_effect = [
        _resp(401, {"error": "no such user"}),
        _resp(200, {"token": "tok-new"}),
    ]
    target = InterviewIQTarget()

    headers = target._headers()

    assert headers == {"Authorization": "Bearer tok-new"}
    assert mock_post.call_count == 2
    assert mock_post.call_args_list[1].args[0].endswith("/api/auth/register")


@patch("redteam.adapters.interview_iq.requests.post")
def test_send_starts_session_then_reuses_it(mock_post):
    mock_post.side_effect = [
        _resp(200, {"token": "tok-123"}),  # login
        _resp(200, {"session": {"_id": "sess-1", "messages": [
            {"role": "interviewer", "content": "Tell me about yourself."},
        ]}}),  # start
        _resp(200, {"session": {"messages": [
            {"role": "interviewer", "content": "Q1"},
            {"role": "candidate", "content": "A1"},
            {"role": "interviewer", "content": "Q2"},
        ]}}),  # answer
    ]
    target = InterviewIQTarget()

    reply = target.send("some attack prompt")

    assert reply == "Q2"
    assert target._session_id == "sess-1"
    answer_call = mock_post.call_args_list[2]
    assert answer_call.args[0].endswith("/api/session/answer")
    assert answer_call.kwargs["json"] == {"sessionId": "sess-1", "answer": "some attack prompt"}


@patch("redteam.adapters.interview_iq.requests.post")
def test_reset_starts_a_new_session_next_send(mock_post):
    mock_post.side_effect = [
        _resp(200, {"token": "tok-123"}),
        _resp(200, {"session": {"_id": "sess-1", "messages": [
            {"role": "interviewer", "content": "Q1"},
        ]}}),
        _resp(200, {"session": {"messages": [{"role": "interviewer", "content": "Q1-reply"}]}}),
    ]
    target = InterviewIQTarget()
    target.send("first")
    target.reset()
    assert target._session_id is None
