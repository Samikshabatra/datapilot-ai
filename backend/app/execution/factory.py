"""Selects the executor implementation from config. The rest of the app asks for
`get_executor()` and never names a concrete class — so V2 flips one config value
(`AAA_EXECUTOR_BACKEND=docker`) with no orchestrator changes."""
from __future__ import annotations

from ..config import settings
from .base import Executor
from .subprocess_executor import SubprocessExecutor


def get_executor() -> Executor:
    backend = settings.executor_backend.lower()
    if backend == "subprocess":
        return SubprocessExecutor(timeout_s=settings.execution_timeout_s)
    if backend == "docker":
        from .docker_executor import DockerExecutor

        return DockerExecutor(
            image=settings.docker_image,
            timeout_s=settings.execution_timeout_s,
            memory=settings.docker_memory,
            cpus=settings.docker_cpus,
            pids_limit=settings.docker_pids_limit,
        )
    raise ValueError(f"Unknown executor backend: {settings.executor_backend!r}")
