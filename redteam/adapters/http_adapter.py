"""Adapter posting prompts to a REST endpoint.

Configurable enough to hit most chat APIs: the prompt is inserted into a JSON body
template, and the reply is pulled out with a dotted JSON path. This is the intended
seam for wiring in the AI interview site later - point it at that site's chat
endpoint, set the request/response paths, done.
"""

from __future__ import annotations

from typing import Any

import requests


class HTTPAdapter:
    """Send prompts to an HTTP JSON endpoint under test."""

    def __init__(
        self,
        url: str,
        *,
        method: str = "POST",
        headers: dict[str, str] | None = None,
        body_template: dict[str, Any] | None = None,
        prompt_field: str = "message",
        response_path: str = "reply",
        timeout: float = 60.0,
        name: str = "http",
    ):
        """
        Args:
            url: Endpoint to call.
            body_template: Base JSON body; the prompt is written into `prompt_field`.
                Defaults to {"<prompt_field>": <prompt>}.
            prompt_field: Key in the body to place the prompt under.
            response_path: Dotted path into the JSON response for the reply text,
                e.g. "choices.0.message.content".
        """
        self.url = url
        self.method = method.upper()
        self.headers = headers or {"Content-Type": "application/json"}
        self.body_template = body_template or {}
        self.prompt_field = prompt_field
        self.response_path = response_path
        self.timeout = timeout
        self.name = name

    def send(self, prompt: str) -> str:
        body = dict(self.body_template)
        body[self.prompt_field] = prompt
        resp = requests.request(
            self.method, self.url, json=body, headers=self.headers, timeout=self.timeout
        )
        resp.raise_for_status()
        return self._extract(resp.json())

    def _extract(self, data: Any) -> str:
        """Walk `response_path` (dot-separated; integer segments index lists)."""
        cur = data
        for segment in self.response_path.split("."):
            if isinstance(cur, list):
                cur = cur[int(segment)]
            elif isinstance(cur, dict):
                cur = cur[segment]
            else:
                raise ValueError(
                    f"Cannot follow '{segment}' in response path '{self.response_path}'"
                )
        return str(cur)
