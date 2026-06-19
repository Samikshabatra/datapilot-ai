"""Concrete LLMClient backed by the Anthropic API (direct calls, no framework)."""
from __future__ import annotations

from anthropic import Anthropic

from .base import LLMClient, LLMResult, LLMUsage


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("AAA_ANTHROPIC_API_KEY is not set.")
        self._client = Anthropic(api_key=api_key)

    def complete(self, prompt: str, *, model: str, max_tokens: int) -> LLMResult:
        msg = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in msg.content if block.type == "text")
        return LLMResult(
            text=text,
            usage=LLMUsage(
                input_tokens=msg.usage.input_tokens,
                output_tokens=msg.usage.output_tokens,
            ),
        )
