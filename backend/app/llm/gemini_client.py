"""Concrete LLMClient backed by the Google Gemini API (direct calls, no framework).

Implements the exact same interface as AnthropicClient, so the orchestrator, the
loop, and every test are unchanged — only deps.get_llm() decides which one to build.
This is the payoff of the provider-agnostic LLMClient boundary.
"""
from __future__ import annotations

import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from .base import LLMClient, LLMResult, LLMUsage

# HTTP statuses worth retrying: transient server overload + rate limiting. Gemini's
# free tier in particular returns 503 ("high demand") and 429 ("quota") in bursts.
_RETRYABLE = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 4  # 1 try + 3 retries
_BASE_DELAY_S = 2.0


class GeminiClient(LLMClient):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("AAA_GEMINI_API_KEY is not set.")
        self._client = genai.Client(api_key=api_key)

    def complete(self, prompt: str, *, model: str, max_tokens: int) -> LLMResult:
        last_err: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = self._client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(max_output_tokens=max_tokens),
                )
                usage = resp.usage_metadata
                return LLMResult(
                    text=resp.text or "",
                    usage=LLMUsage(
                        input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                        output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
                    ),
                )
            except genai_errors.APIError as e:
                # Retry transient overload/rate-limit with exponential backoff;
                # re-raise anything else (bad key, invalid request) immediately.
                if getattr(e, "code", None) not in _RETRYABLE or attempt == _MAX_ATTEMPTS - 1:
                    raise
                last_err = e
                time.sleep(_BASE_DELAY_S * (2 ** attempt))  # 2s, 4s, 8s
        raise last_err  # unreachable, but keeps type-checkers happy
