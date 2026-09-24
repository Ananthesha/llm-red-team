"""Adapter for InterviewIQ (the paired resume project).

Unlike HTTPAdapter (one stateless POST), InterviewIQ's chat flow is stateful:
authenticate once, start an interview session, then send each attack prompt as an
"answer" and read the interviewer's next question back. Each `send()` call is one
turn in an ongoing session - the adapter owns the session/auth lifecycle so the rest
of the toolkit still just sees `send(prompt) -> str`.

Uses a dedicated test account (register-or-login), never the operator's personal
InterviewIQ login. Every call is a real request against a running InterviewIQ server
and triggers a real Groq/Gemini API call on that project's own keys - point this at
a local dev server, not the deployed one, unless you mean to spend that quota.
"""

from __future__ import annotations

import requests


class InterviewIQTarget:
    """Sends attack prompts as interview answers and returns the next question."""

    name = "interview-iq"

    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        *,
        email: str = "eval-harness@example.com",
        password: str = "password123",
        company_persona: str = "General",
        target_role: str = "Software Engineer",
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.company_persona = company_persona
        self.target_role = target_role
        self.timeout = timeout
        self._token: str | None = None
        self._session_id: str | None = None

    # -- auth -----------------------------------------------------------

    def _login_or_register(self) -> str:
        resp = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": self.email, "password": self.password},
            timeout=self.timeout,
        )
        if resp.status_code == 200:
            return resp.json()["token"]

        resp = requests.post(
            f"{self.base_url}/api/auth/register",
            json={"name": "Eval Harness", "email": self.email, "password": self.password},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["token"]

    def _headers(self) -> dict[str, str]:
        if self._token is None:
            self._token = self._login_or_register()
        return {"Authorization": f"Bearer {self._token}"}

    # -- session lifecycle ------------------------------------------------

    def _start_session(self) -> str:
        resp = requests.post(
            f"{self.base_url}/api/session/start",
            json={"companyPersona": self.company_persona, "targetRole": self.target_role},
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        session = resp.json()["session"]
        return session["_id"]

    def reset(self) -> None:
        """Start a fresh interview session on the next `send()` call.

        Call this between independent test cases so one attack prompt's fallout
        (e.g. a derailed persona) doesn't bleed into the next test case's turn.
        """
        self._session_id = None

    # -- TargetAdapter protocol -------------------------------------------

    def send(self, prompt: str) -> str:
        if self._session_id is None:
            self._session_id = self._start_session()

        resp = requests.post(
            f"{self.base_url}/api/session/answer",
            json={"sessionId": self._session_id, "answer": prompt},
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        messages = resp.json()["session"]["messages"]
        interviewer_messages = [m for m in messages if m.get("role") == "interviewer"]
        if not interviewer_messages:
            return ""
        return interviewer_messages[-1].get("content", "")
