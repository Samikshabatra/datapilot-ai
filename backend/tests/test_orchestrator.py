"""Orchestrator tests — the self-correction loop, driven by a scripted fake LLM and
the REAL subprocess executor. No API key required, so this runs in CI.
"""
from __future__ import annotations

from app.core.orchestrator import Orchestrator
from app.core.response import LoopState
from app.execution.subprocess_executor import SubprocessExecutor
from app.llm.base import LLMClient, LLMResult, LLMUsage


class ScriptedLLM(LLMClient):
    """Returns a pre-set sequence of responses, one per call."""

    def __init__(self, responses: list[str]):
        self._responses = responses
        self.calls = 0

    def complete(self, prompt: str, *, model: str, max_tokens: int) -> LLMResult:
        text = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        return LLMResult(text=text, usage=LLMUsage())


def _orch(responses):
    return Orchestrator(llm=ScriptedLLM(responses), executor=SubprocessExecutor(timeout_s=15))


def test_succeeds_first_try(sample_csv):
    # 1st response = code, 2nd = the synthesis (expert narrative) call.
    orch = _orch([
        "```python\n# reasoning: sum revenue\nresult = int(df['revenue'].sum())\n```",
        "Total revenue across all regions is **875**.",
    ])
    resp = orch.run(schema="(schema)", question="total revenue?", data_path=sample_csv)
    assert resp.state == LoopState.DONE
    assert resp.answer == "Total revenue across all regions is **875**."  # synthesized answer
    assert resp.attempts[-1].result_repr == "875"  # raw computed value preserved
    assert len(resp.attempts) == 1


def test_self_corrects_after_error(sample_csv):
    bad = "```python\n# reasoning: wrong col\nresult = df['sales'].sum()\n```"
    good = "```python\n# reasoning: fixed col\nresult = int(df['revenue'].sum())\n```"
    synth = "The total revenue is 875."
    orch = _orch([bad, good, synth])
    resp = orch.run(schema="(schema)", question="total revenue?", data_path=sample_csv)
    assert resp.state == LoopState.DONE
    assert resp.answer == synth
    assert resp.attempts[-1].result_repr == "875"
    assert len(resp.attempts) == 2  # failed once, then recovered


def test_gives_up_on_repeated_identical_error(sample_csv):
    bad = "```python\nresult = df['sales'].sum()\n```"
    # same error every time -> should short-circuit, not exhaust full budget
    orch = _orch([bad, bad, bad, bad])
    resp = orch.run(schema="(schema)", question="x?", data_path=sample_csv)
    assert resp.state == LoopState.FAILED
    assert len(resp.attempts) == 2  # stopped after detecting the repeat


def test_needs_clarification_path(sample_csv):
    clarify = "```python\nresult = 'CLARIFY: there is no churn column in this dataset'\n```"
    orch = _orch([clarify])
    resp = orch.run(schema="(schema)", question="what drives churn?", data_path=sample_csv)
    assert resp.state == LoopState.NEEDS_CLARIFICATION
    assert "churn" in resp.error
