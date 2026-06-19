---
title: DataPilot AI — Autonomous Data Analyst
emoji: 🧭
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Autonomous Data Analyst Agent

Upload a dataset, ask a question in plain language. An agent writes Python, runs it
in a sandbox, **observes the result, and self-corrects on errors** — then returns the
answer, a chart, and the exact code that produced it. Every step is verifiable.

The defensible mechanism: **write code → execute → observe → self-correct.**

## Status — V1 (the core loop)

| Capability | State |
|---|---|
| CSV / Excel upload + schema profiling (schema-not-data to the LLM) | ✅ |
| Prompt assembly from versioned templates | ✅ |
| Code generation via Anthropic (direct API, no framework) | ✅ |
| Sandboxed execution (separate process, hard timeout, scrubbed env) | ✅ |
| Self-correction loop with smart exit (same-error / clarify-vs-retry) | ✅ |
| Transparent response: answer + chart + code + full attempt trail | ✅ |
| Streamlit UI | ✅ |

## Status — V2 (making it a product)

| Capability | State |
|---|---|
| Docker sandbox: per-run container, no network, capped CPU/mem, read-only FS | ✅ |
| Provider-agnostic LLM layer (Gemini active; Anthropic fallback) | ✅ |
| Tabular results rendered as real tables | ✅ |
| ML-engineer proficiency: sklearn/scipy/statsmodels/seaborn + senior-DS prompt | ✅ |
| Answer synthesis: expert interpretation of the computed result (not raw values) | ✅ |
| Conversation memory: follow-up questions resolve against prior turns | ✅ |
| Auto-EDA on upload (instant overview, reuses the engine) | ✅ |
| Deploy to public URL | ⏳ |

V3 (ML on request as a first-class feature, forecasting, caching) is scoped in
[`docs/architecture.md`](docs/architecture.md).

## Architecture at a glance

```
Frontend (Streamlit) → FastAPI → Orchestrator (state machine)
                                    ├─ Profiler      (schema the LLM sees)
                                    ├─ Prompt Builder (versioned templates)
                                    ├─ LLM Client     (provider-agnostic)
                                    └─ Executor       (interface: subprocess→Docker)
                                         ↑ the one pluggable boundary
```

The **Executor interface** is the key decision: the orchestrator never knows whether
code ran in a subprocess (V1) or a Docker container (V2). Swapping sandboxes is a
config flip, not a rewrite. See [`docs/decisions/`](docs/decisions/).

## Run it

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate        # Windows
pip install -e ".[frontend,dev]"

# tests — no API key needed (mock LLM + real sandbox)
pytest

# backend (this project uses port 8010; 8000 is often held by Docker/WSL forwards)
copy ..\.env.example .env       # add your AAA_GEMINI_API_KEY
uvicorn app.main:app --reload --port 8010

# frontend (separate terminal) — defaults to talking to localhost:8010
streamlit run ..\frontend\streamlit_app.py
```

Then open the Streamlit URL, upload `sample_data/sales.csv`, and ask:
*"Which region has the highest total revenue?"* or *"Plot revenue over time."*

## V2 — Docker sandbox (real isolation)

The `DockerExecutor` implements the same `Executor` interface as V1, so switching is
a config flip — the orchestrator and loop are unchanged. Each question runs in a fresh
container: `--network none`, capped memory/CPU, `--pids-limit`, read-only filesystem
(+ small tmpfs), non-root user, dataset mounted read-only, container destroyed after.

```powershell
# 1. Start Docker Desktop (from the Start menu) and wait for "Engine running".
# 2. Build the sandbox image (run from backend/, the build context):
docker build -t aaa-sandbox:latest -f sandbox/Dockerfile.runner .

# 3. Switch the backend to docker in backend/.env:
#      AAA_EXECUTOR_BACKEND=docker
# 4. Restart uvicorn. That's it — same loop, real isolation.
```

To go back to the V1 subprocess sandbox, set `AAA_EXECUTOR_BACKEND=subprocess`.

## Honest note on the V1 sandbox

The V1 executor is a **separate process with a hard timeout and a scrubbed
environment** — enough to stop runaway code and keep secrets out of generated code.
It is **not** a security boundary: a subprocess can still reach the filesystem and
network. Real isolation (no network, capped CPU/memory, ephemeral filesystem) is the
`DockerExecutor` in V2, which implements the same interface. Naming this limit is
deliberate — see [`docs/security.md`](docs/security.md).
