# ADR 0001 — Executor as a pluggable interface from day one

**Status:** accepted (V1)

## Context
The roadmap moves execution from a subprocess (Phase 1) to a Docker container (Phase 2).
If V1 hardcodes subprocess calls in the orchestrator, the V2 sandbox becomes a rewrite.

## Decision
Define `Executor` as an abstract interface — `execute(code, data_path) -> ExecutionResult`
— with `SubprocessExecutor` (V1) and `DockerExecutor` (V2) as implementations selected by
a factory from config (`AAA_EXECUTOR_BACKEND`). The orchestrator depends only on the
interface and never names a concrete class.

## Consequences
- V2 sandbox is a config flip, not a rewrite.
- The sandbox is unit-testable without Docker in CI (subprocess used in tests).
- `ExecutionResult` is data-only and serializable, so it crosses a process/container
  boundary unchanged.
- Small upfront cost: one extra interface + factory. Paid back entirely at V2.
