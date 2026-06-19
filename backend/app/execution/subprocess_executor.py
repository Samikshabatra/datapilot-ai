"""V1 executor: runs generated code in a separate OS process under a hard timeout.

Isolation properties (and honest non-properties):
  - SEPARATE PROCESS: user code cannot touch the API server's memory or objects.
  - HARD WALL-CLOCK TIMEOUT: the process is killed if it runs too long. This is the
    real boundary in V1 — it stops infinite loops and runaway compute.
  - CLEAN ENV: the child is launched with a scrubbed environment so API keys and
    other secrets are never visible to generated code.
  - NOT a security sandbox: a subprocess can still read the local filesystem and
    open sockets. Real isolation (no network, capped CPU/mem, ephemeral FS) arrives
    in V2 via DockerExecutor, which implements this same interface.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .base import ExecutionResult, Executor

_RUNNER = Path(__file__).resolve().parent / "runner.py"


class SubprocessExecutor(Executor):
    def __init__(self, timeout_s: int = 30):
        self.timeout_s = timeout_s

    def execute(self, code: str, data_path: str) -> ExecutionResult:
        start = time.perf_counter()
        # The sandbox runs with cwd=tmp for isolation, so the data path MUST be
        # absolute — a relative path would resolve against the throwaway temp dir
        # and vanish.
        abs_data_path = str(Path(data_path).resolve())
        with tempfile.TemporaryDirectory() as tmp:
            payload_path = Path(tmp) / "payload.json"
            result_path = Path(tmp) / "result.json"
            payload_path.write_text(
                json.dumps({"code": code, "data_path": abs_data_path}), encoding="utf-8"
            )

            # Scrubbed environment: keep PATH/system vars, drop everything app-specific.
            clean_env = {
                k: v
                for k, v in os.environ.items()
                if k in {"PATH", "SYSTEMROOT", "TEMP", "TMP", "PATHEXT", "PYTHONHOME"}
                or k.startswith("PYTHON")
            }
            clean_env["MPLBACKEND"] = "Agg"
            clean_env["MPLCONFIGDIR"] = tmp  # writable matplotlib cache dir (any host)

            try:
                subprocess.run(
                    [sys.executable, str(_RUNNER), str(payload_path), str(result_path)],
                    timeout=self.timeout_s,
                    capture_output=True,
                    env=clean_env,
                    cwd=tmp,  # confine working dir to the throwaway temp dir
                )
            except subprocess.TimeoutExpired:
                return ExecutionResult(
                    ok=False,
                    error=f"Execution exceeded the {self.timeout_s}s time limit and was killed.",
                    timed_out=True,
                    duration_s=time.perf_counter() - start,
                )

            duration = time.perf_counter() - start
            if not result_path.exists():
                return ExecutionResult(
                    ok=False,
                    error="Sandbox produced no result (the process likely crashed hard).",
                    duration_s=duration,
                )

            data = json.loads(result_path.read_text(encoding="utf-8"))
            return ExecutionResult(
                ok=data["ok"],
                stdout=data.get("stdout", ""),
                result_repr=data.get("result_repr", ""),
                error=data.get("error"),
                chart_png_base64=data.get("chart_png_base64"),
                result_kind=data.get("result_kind", "scalar"),
                result_table=data.get("result_table"),
                duration_s=duration,
            )
