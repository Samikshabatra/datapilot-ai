"""The response contract.

Every answer the agent returns conforms to this shape, whether it succeeded on
the first try or after three self-corrections. Transparency is structural here:
the code, the reasoning, and every attempt are part of the payload, never bolted
on afterward.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LoopState(str, Enum):
    """Explicit states of the core loop. Used for tracing and for deciding
    whether the agent should retry, ask the human, or stop."""

    PROFILING = "profiling"
    GENERATING = "generating"
    EXECUTING = "executing"
    OBSERVING = "observing"
    CORRECTING = "correcting"
    DONE = "done"
    FAILED = "failed"
    NEEDS_CLARIFICATION = "needs_clarification"


class Attempt(BaseModel):
    """A single trip around the loop: the code we ran and what came back.

    Keeping every attempt lets the UI show the full self-correction trail, which
    is the most convincing demonstration that this is an agent, not a code emitter.
    """

    index: int
    code: str
    reasoning: str = ""
    stdout: str = ""
    result_repr: str = ""
    error: Optional[str] = None
    chart_png_base64: Optional[str] = None
    duration_s: float = 0.0


class AgentResponse(BaseModel):
    """The transparent triple (+ trail) returned for every question."""

    state: LoopState
    answer: str = ""  # natural-language answer
    code: str = ""  # the exact code that produced the final answer
    reasoning: str = ""  # why the agent wrote that code
    chart_png_base64: Optional[str] = None  # rendered chart, if any
    result_kind: str = "scalar"  # "scalar" | "dataframe" — how the UI should render
    result_table: Optional[str] = None  # JSON (orient="split") when result is tabular
    attempts: list[Attempt] = Field(default_factory=list)
    error: Optional[str] = None  # populated only on FAILED / NEEDS_CLARIFICATION

    @property
    def succeeded(self) -> bool:
        return self.state == LoopState.DONE
