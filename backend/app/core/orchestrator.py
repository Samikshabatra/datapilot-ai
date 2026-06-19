"""The core loop, as an explicit state machine.

    PROFILING (done at upload) -> GENERATING -> EXECUTING -> OBSERVING
                                       ^                          |
                                       |        self-correct      |
                                       +-----------(<= N)---------+
                                                                  |
                                          DONE | FAILED | NEEDS_CLARIFICATION

This is the single most important thing to get right — the self-correction cycle
is what separates a real agent from an "LLM that emits code" demo. Two refinements
beyond a naive retry counter:

  1. Same-error short-circuit: if two consecutive attempts fail with the same error
     signature, we stop early instead of burning the full retry budget repeating a
     fix that clearly isn't working.
  2. Retry vs. ask-the-human: if the model signals the question can't be answered
     from this data (a `CLARIFY:` result), we surface that to the user rather than
     looping. Knowing when NOT to retry is part of being a good agent.
"""
from __future__ import annotations

from ..config import settings
from ..execution.base import Executor, ExecutionResult
from ..llm.base import LLMClient, extract_code, extract_reasoning
from . import prompt_builder as pb
from .response import AgentResponse, Attempt, LoopState


class Orchestrator:
    def __init__(self, llm: LLMClient, executor: Executor):
        self.llm = llm
        self.executor = executor

    def run(self, schema: str, question: str, data_path: str, history: str = "") -> AgentResponse:
        attempts: list[Attempt] = []
        prompt = pb.build_generate_prompt(schema, question, history)
        model = settings.model_generate
        last_code: str | None = None

        for i in range(settings.max_retries + 1):  # 1 initial + N corrections
            # --- GENERATING ---
            # An LLM-side failure (auth, billing, rate limit, network) is not the
            # agent being "wrong" — there is nothing to self-correct. Surface it
            # cleanly as a FAILED response instead of bubbling up a raw 500.
            try:
                llm_out = self.llm.complete(prompt, model=model, max_tokens=settings.max_tokens)
            except Exception as e:  # noqa: BLE001 — provider exceptions vary
                return AgentResponse(
                    state=LoopState.FAILED,
                    attempts=attempts,
                    error=f"The model could not be reached: {type(e).__name__}: {e}",
                )
            code = extract_code(llm_out.text)
            reasoning = extract_reasoning(code)

            # --- EXECUTING ---
            exec_result: ExecutionResult = self.executor.execute(code, data_path)

            attempt = Attempt(
                index=i,
                code=code,
                reasoning=reasoning,
                stdout=exec_result.stdout,
                result_repr=exec_result.result_repr,
                error=exec_result.error,
                chart_png_base64=exec_result.chart_png_base64,
                duration_s=exec_result.duration_s,
            )
            attempts.append(attempt)

            # --- OBSERVING ---
            if exec_result.ok:
                # The model can signal "I can't answer this from the data."
                if exec_result.result_repr.startswith(("'CLARIFY:", '"CLARIFY:')):
                    msg = exec_result.result_repr.strip("'\"").removeprefix("CLARIFY:").strip()
                    return AgentResponse(
                        state=LoopState.NEEDS_CLARIFICATION,
                        reasoning=reasoning,
                        code=code,
                        attempts=attempts,
                        error=msg,
                    )
                return AgentResponse(
                    state=LoopState.DONE,
                    answer=self._synthesize(question, code, exec_result),
                    code=code,
                    reasoning=reasoning,
                    chart_png_base64=exec_result.chart_png_base64,
                    result_kind=exec_result.result_kind,
                    result_table=exec_result.result_table,
                    attempts=attempts,
                )

            # --- failure: decide whether to CORRECT, or give up ---
            # Only bail early if the model retried the EXACT same code (genuinely
            # stuck / looping). If it's producing different code each time it's
            # making real attempts — let it use the full retry budget. (Comparing
            # error messages was too aggressive: different buggy code often yields
            # the same SyntaxError text, which killed recoverable cases.)
            if code == last_code:
                break
            last_code = code

            if i == settings.max_retries:
                break  # budget exhausted

            # --- CORRECTING: feed the traceback back in, switch to the cheap model ---
            prompt = pb.build_correction_prompt(schema, question, code, exec_result.error or "")
            model = settings.model_correct

        return AgentResponse(
            state=LoopState.FAILED,
            code=attempts[-1].code if attempts else "",
            reasoning=attempts[-1].reasoning if attempts else "",
            attempts=attempts,
            error=(attempts[-1].error if attempts else "No attempts were made."),
        )

    def _synthesize(self, question: str, code: str, r: ExecutionResult) -> str:
        """Turn the raw computed result into an expert, natural-language answer —
        the difference between a calculator and an analyst. Falls back to the raw
        result if the synthesis call fails (e.g. rate limit), so an answer is
        always returned."""
        raw = self._raw_result(r)
        if not settings.synthesize_answers:
            return raw  # quota-saving mode: skip the extra LLM call
        try:
            prompt = pb.build_synthesis_prompt(question, code, r.stdout, raw)
            out = self.llm.complete(prompt, model=settings.model_generate, max_tokens=settings.max_tokens)
            text = out.text.strip()
            return text or raw
        except Exception:  # noqa: BLE001 — never let synthesis sink a good answer
            return raw

    @staticmethod
    def _raw_result(r: ExecutionResult) -> str:
        """The bare computed value, used for synthesis input and as fallback."""
        if r.result_repr:
            return r.result_repr
        if r.stdout.strip():
            return r.stdout.strip()
        return "(The code ran successfully but produced no `result` or output.)"
