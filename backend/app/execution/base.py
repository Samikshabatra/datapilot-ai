"""Executor interface — the one pluggable boundary in the system.

The orchestrator calls `execute(code, data_path)` and never knows whether the code
ran in a subprocess (V1) or a locked-down Docker container (V2). Keeping this
contract stable is what turns the V2 "real sandbox" from a rewrite into a swap.

ExecutionResult is deliberately data-only and serializable so it can cross a
process or container boundary unchanged.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    ok: bool
    stdout: str = ""
    result_repr: str = ""  # repr() of the user code's `result` variable
    error: Optional[str] = None  # traceback text, fed back to the model on failure
    chart_png_base64: Optional[str] = None  # captured matplotlib figure, if any
    result_kind: str = "scalar"  # "scalar" | "dataframe"
    result_table: Optional[str] = None  # JSON (orient="split") when result is tabular
    timed_out: bool = False
    duration_s: float = 0.0


class Executor(ABC):
    @abstractmethod
    def execute(self, code: str, data_path: str) -> ExecutionResult:
        """Run `code` with a dataframe `df` loaded from `data_path`, in isolation,
        under a hard timeout. Never raises on user-code failure — failures come
        back inside ExecutionResult.error so the loop can self-correct on them."""
        raise NotImplementedError
