"""Provider-agnostic LLM interface.

The orchestrator depends only on this. Swapping providers, or adding a framework
later, means adding an implementation here — not touching the loop. We deliberately
start with direct API calls (no LangChain): a 4-step loop does not need an agent
framework, and the abstraction cost would exceed the loop's own complexity.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMResult:
    text: str
    usage: LLMUsage


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, model: str, max_tokens: int) -> LLMResult:
        """Single-shot completion. The loop is stateful at the orchestrator level,
        so the client itself stays stateless and trivially mockable in tests."""
        raise NotImplementedError


_CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Pull the first fenced python block out of a model response.
    Falls back to the raw text if the model forgot the fences."""
    m = _CODE_BLOCK.search(text)
    return (m.group(1) if m else text).strip()


def extract_reasoning(code: str) -> str:
    """The templates ask the model to start with a `# reasoning:` line."""
    for line in code.splitlines():
        s = line.strip()
        if s.lower().startswith("# reasoning:"):
            return s.split(":", 1)[1].strip()
    return ""
