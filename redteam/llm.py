"""Thin shared wrapper over two interchangeable LLM providers: Groq and Gemini.

Centralises model choice and the API-key check so the generator, judge, and sample
target don't each reimplement it. Two providers exist because Groq's free tier has a
hard daily token cap (200K TPD) that a single evaluation run can hit mid-suite -
Gemini is a second, independently-capped free tier to fall back to rather than
stalling for hours. Reads GROQ_API_KEY / GEMINI_API_KEY from the environment.

Default provider is Groq (kept as the primary since it's fast and the toolkit was
built against it); pass provider="gemini" per-call, or set REDTEAM_PROVIDER=gemini
to switch the default globally (e.g. when Groq's daily cap is exhausted).
"""

from __future__ import annotations

import os
import re
import time
from functools import lru_cache

# openai/gpt-oss-120b is Groq's recommended replacement for the deprecated
# llama-3.3-70b-versatile (deprecated June 2026) - strong general reasoning, good
# instruction following, available on the free tier.
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


class MissingAPIKey(RuntimeError):
    """Raised when the selected provider's API key is not set."""


def default_provider() -> str:
    return os.environ.get("REDTEAM_PROVIDER", "groq")


@lru_cache(maxsize=1)
def _groq_client():
    if not os.environ.get("GROQ_API_KEY"):
        raise MissingAPIKey(
            "GROQ_API_KEY is not set. Export it before running:\n"
            "  export GROQ_API_KEY=gsk_..."
        )
    # Imported lazily so `--help` and unit tests that mock the LLM don't require
    # the groq package or a key to be present.
    from groq import Groq

    return Groq()


@lru_cache(maxsize=1)
def _gemini_client():
    if not os.environ.get("GEMINI_API_KEY"):
        raise MissingAPIKey(
            "GEMINI_API_KEY is not set. Export it before running:\n"
            "  export GEMINI_API_KEY=AIza..."
        )
    from google import genai

    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def get_client(provider: str | None = None):
    """Return a cached client for the given (or default) provider."""
    provider = provider or default_provider()
    if provider == "groq":
        return _groq_client()
    if provider == "gemini":
        return _gemini_client()
    raise ValueError(f"Unknown provider '{provider}'. Use 'groq' or 'gemini'.")


def _complete_groq(
    client,
    prompt: str,
    *,
    system: str | None,
    model: str,
    max_tokens: int,
    temperature: float,
    retries: int,
    reasoning_effort: str | None,
) -> str:
    """`openai/gpt-oss-120b` is a reasoning model: it can spend most or all of
    `max_tokens` on an internal `reasoning` field before writing the final answer
    into `content`, which then comes back empty (`finish_reason == "length"`). We
    default `max_tokens` high enough to leave room for both, and as a safety net
    fall back to the reasoning text if content is ever empty.

    `reasoning_effort="low"` keeps reasoning tokens to a handful instead of ~100 per
    call, which matters a lot against the free tier's 6,000 tokens/min cap.

    Retries on rate-limit (429) errors with exponential backoff. Note this only
    covers the per-minute cap with a short backoff; Groq's free tier also has a much
    larger *daily* token cap (200K TPD) that a short backoff cannot wait out - that
    shows up as a 429 whose retry-after is minutes, not seconds, and this will
    eventually re-raise it rather than block for hours. Switch provider="gemini" (or
    REDTEAM_PROVIDER=gemini) when that happens.
    """
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


# Some Gemini free-tier projects cap gemini-2.5-flash as low as 5 requests/minute
# (observed directly, well under Google's documented default). Rather than only
# reacting to 429s after the fact, space calls out proactively so most of them
# never trip the limit in the first place; the 429/retryDelay handling in
# _complete_gemini remains as a fallback for whatever the pacing doesn't catch.
_GEMINI_MIN_INTERVAL_S = 13.0
_gemini_last_call_at = 0.0


def _complete_gemini(
    client,
    prompt: str,
    *,
    system: str | None,
    model: str,
    max_tokens: int,
    temperature: float,
    retries: int,
) -> str:
    """Some Gemini free-tier projects get a low per-minute request quota for
    gemini-2.5-flash (observed as low as 5 RPM), well under Groq's 30 RPM. The
    429 response includes a `retryDelay` (seconds) telling us exactly how long to
    wait - we parse and use that instead of a fixed backoff schedule, since a
    generic 2/4/8s backoff isn't long enough to clear a "retry in 27s" quota error.
    """
    global _gemini_last_call_at

    from google.genai import types

    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        temperature=temperature,
        system_instruction=system,
    )
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        wait_for_pacing = _GEMINI_MIN_INTERVAL_S - (time.time() - _gemini_last_call_at)
        if wait_for_pacing > 0:
            time.sleep(wait_for_pacing)
        try:
            _gemini_last_call_at = time.time()
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
            return (resp.text or "").strip()
        except Exception as exc:  # noqa: BLE001 - retry generically, re-raise at end
            last_exc = exc
            msg = str(exc)
            is_rate_limit = "429" in msg or "RESOURCE_EXHAUSTED" in msg
            if attempt < retries and is_rate_limit:
                wait = _parse_retry_delay(msg) or (2 ** (attempt + 2))
                time.sleep(wait + 1)  # +1s safety margin past the server's own estimate
                continue
            raise
    raise last_exc  # pragma: no cover - unreachable, satisfies type checkers


def _parse_retry_delay(error_message: str) -> float | None:
    """Extract the seconds from a Gemini 429's `'retryDelay': '27s'` field."""
    match = re.search(r"'retryDelay':\s*'(\d+(?:\.\d+)?)s'", error_message)
    return float(match.group(1)) if match else None


def complete(
    prompt: str,
    *,
    system: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 1.0,
    retries: int = 4,
    reasoning_effort: str | None = "low",
) -> str:
    """Send a single-turn message and return the assistant's text.

    `provider` picks "groq" (default) or "gemini"; `model` defaults to each
    provider's own default model if not given. `reasoning_effort` only applies to
    Groq's reasoning model and is ignored for Gemini.
    """
    provider = provider or default_provider()
    client = get_client(provider)

    if provider == "groq":
        return _complete_groq(
            client,
            prompt,
            system=system,
            model=model or DEFAULT_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            retries=retries,
            reasoning_effort=reasoning_effort,
        )
    if provider == "gemini":
        return _complete_gemini(
            client,
            prompt,
            system=system,
            model=model or DEFAULT_GEMINI_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            retries=retries,
        )
    raise ValueError(f"Unknown provider '{provider}'. Use 'groq' or 'gemini'.")
