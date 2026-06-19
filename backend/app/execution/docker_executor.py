"""V2 executor: runs generated code in a fresh, locked-down Docker container.

This is the headline isolation story. Same `Executor` interface as the V1
subprocess executor, so the orchestrator and the loop are completely unchanged —
swapping sandboxes is a config flip (`AAA_EXECUTOR_BACKEND=docker`).

Each run gets a brand-new container with:
  --network none        no network access at all
  --memory / --cpus     hard resource caps (OOM-killed on breach)
  --pids-limit          fork-bomb guard
  --read-only + tmpfs   immutable filesystem except a small /tmp scratch
  non-root user         baked into the image
The dataset is mounted read-only; results return via a mounted work dir. The
container is destroyed after each run (ephemeral filesystem).
"""
from __future__ import annotations

import json
import subprocess
import time
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from ..config import settings
from .base import ExecutionResult, Executor


def _to_docker_path(p: str | Path) -> str:
    """Docker Desktop on Windows accepts forward-slash paths with a drive letter
    (C:/Users/...). Normalise backslashes so bind mounts parse reliably."""
    return str(Path(p).resolve()).replace("\\", "/")


class DockerExecutor(Executor):
    def __init__(
        self,
        image: str,
        timeout_s: int,
        memory: str = "512m",
        cpus: str = "1.0",
        pids_limit: int = 256,
    ):
        self.image = image
        self.timeout_s = timeout_s
        self.memory = memory
        self.cpus = cpus
        self.pids_limit = pids_limit

    def execute(self, code: str, data_path: str) -> ExecutionResult:
        start = time.perf_counter()
        suffix = Path(data_path).suffix or ".csv"
        container_data = f"/data/input{suffix}"
        name = f"aaa-sandbox-{uuid.uuid4().hex[:12]}"

        with TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "payload.json").write_text(
                json.dumps({"code": code, "data_path": container_data}), encoding="utf-8"
            )

            cmd = [
                "docker", "run", "--rm", "--name", name,
                "--network", "none",
                "--memory", self.memory, "--cpus", self.cpus,
                "--pids-limit", str(self.pids_limit),
                "--read-only", "--tmpfs", "/tmp:size=128m,exec",
                "-v", f"{_to_docker_path(work)}:/work",
                "-v", f"{_to_docker_path(data_path)}:{container_data}:ro",
                self.image,
                "/work/payload.json", "/work/result.json",
            ]

            try:
                proc = subprocess.run(cmd, timeout=self.timeout_s, capture_output=True, text=True)
            except subprocess.TimeoutExpired:
                # The container is still alive; kill it so it can't linger.
                subprocess.run(["docker", "rm", "-f", name], capture_output=True)
                return ExecutionResult(
                    ok=False,
                    error=f"Execution exceeded the {self.timeout_s}s time limit and was killed.",
                    timed_out=True,
                    duration_s=time.perf_counter() - start,
                )

            duration = time.perf_counter() - start
            result_file = work / "result.json"
            if not result_file.exists():
                # No result usually means an infra problem (image missing, OOM kill,
                # daemon error) rather than a user-code error — surface docker's stderr.
                stderr = (proc.stderr or "").strip()
                hint = ""
                if "Unable to find image" in stderr or "No such image" in stderr:
                    hint = (" — the sandbox image is missing. Build it with:\n"
                            "    docker build -t aaa-sandbox:latest -f sandbox/Dockerfile.runner .")
                return ExecutionResult(
                    ok=False,
                    error=f"Sandbox produced no result (exit {proc.returncode}).{hint}\n{stderr}",
                    duration_s=duration,
                )

            data = json.loads(result_file.read_text(encoding="utf-8"))
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
