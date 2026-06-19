"""Shared dependencies — LLM client + executor wiring, so routes stay thin.

Supports BYOK (bring your own key): a per-request API key (sent as a header by the
frontend) takes precedence over the server's configured key. This lets the public
demo run without the owner's key on the server — each visitor supplies their own.
"""
from __future__ import annotations

from ..config import settings
from ..core.orchestrator import Orchestrator
from ..execution.factory import get_executor
from ..llm.base import LLMClient


def build_llm(api_key: str | None = None) -> LLMClient:
    """Build the configured provider's client. A non-empty `api_key` (from the
    request) overrides the server's env key; otherwise the env key is used."""
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        from ..llm.gemini_client import GeminiClient

        return GeminiClient(api_key=(api_key or settings.gemini_api_key))
    if provider == "anthropic":
        from ..llm.anthropic_client import AnthropicClient

        return AnthropicClient(api_key=(api_key or settings.anthropic_api_key))
    raise ValueError(f"Unknown llm_provider: {settings.llm_provider!r}")


def build_orchestrator(api_key: str | None = None) -> Orchestrator:
    return Orchestrator(llm=build_llm(api_key), executor=get_executor())
