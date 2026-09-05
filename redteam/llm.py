"""Thin shared wrapper around the Groq client.

Centralises model choice and the API-key check so the generator, judge, and sample
target don't each reimplement it. Reads GROQ_API_KEY from the environment.

Groq's free tier is genuinely free (no credit card) but rate-limited - by default
30 requests/min and 6,000 tokens/min per model. `complete()` retries with backoff on
429s so a full suite run doesn't die the first time it's throttled; callers running
many calls in a loop (generator, judge) should still expect a run to take a few
minutes on the free tier.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache

# openai/gpt-oss-120b is Groq's recommended replacement for the deprecated
# llama-3.3-70b-versatile (deprecated June 2026) - strong general reasoning, good
# instruction following, available on the free tier.
DEFAULT_MODEL = "openai/gpt-oss-120b"


class MissingAPIKey(RuntimeError):
    """Raised when GROQ_API_KEY is not set."""


@lru_cache(maxsize=1)
def get_client():
    """Return a cached Groq client, or raise a clear error if unconfigured."""
    if not os.environ.get("GROQ_API_KEY"):
        raise MissingAPIKey(
            "GROQ_API_KEY is not set. Export it before running:\n"
            "  export GROQ_API_KEY=gsk_..."
        )
    # Imported lazily so `--help` and unit tests that mock the LLM don't require
    # the groq package or a key to be present.
    from groq import Groq

    return Groq()


def complete(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
    temperature: float = 1.0,
    retries: int = 4,
    reasoning_effort: str | None = "low",
) -> str:
    """Send a single-turn message and return the assistant's text.

    `openai/gpt-oss-120b` (the default model) is a reasoning model: it can spend
    most or all of `max_tokens` on an internal `reasoning` field before writing the
    final answer into `content`, which then comes back empty (`finish_reason ==
    "length"`). We default `max_tokens` high enough to leave room for both, and as
    a safety net fall back to the reasoning text if content is ever empty so a
    truncated response degrades gracefully instead of returning nothing.

    `reasoning_effort="low"` (the default) keeps reasoning tokens to a handful
    instead of ~100 per call, which matters a lot against the free tier's 6,000
    tokens/min cap. Pass None to let the model reason at its own default depth.

    Retries on rate-limit (429) errors with exponential backoff, since the Groq
    free tier is capped at 30 req/min per model.
    """
    client = get_client()
    messages = []
    if system is not None:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if reasoning_effort is not None:
        kwargs["reasoning_effort"] = reasoning_effort

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(**kwargs)
            message = resp.choices[0].message
            content = (message.content or "").strip()
            if content:
                return content
            reasoning = (getattr(message, "reasoning", None) or "").strip()
            return reasoning
        except Exception as exc:  # noqa: BLE001 - retry generically, re-raise at end
            last_exc = exc
            status = getattr(exc, "status_code", None)
            is_rate_limit = status == 429 or "rate" in str(exc).lower()
            if attempt < retries and is_rate_limit:
                wait = 2**attempt * 2  # 2s, 4s, 8s, 16s
                time.sleep(wait)
                continue
            raise
    raise last_exc  # pragma: no cover - unreachable, satisfies type checkers
