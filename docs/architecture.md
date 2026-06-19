# Architecture

## Mental model

Everything is **one loop on a server**, with a thin chat UI in front and a sandbox
underneath:

```
1. User question (+ schema) → 2. LLM writes Python/SQL → 3. Sandbox executes
        ↑                                                          │
        └──────────────── 4. Observe result / error ──────────────┘
                          (loop closes on itself, ≤3 retries)
```

The self-correction cycle (step 4 → step 2) is the defensible mechanism. It is the
single most important thing to get right.

## Components

| Component | File | Responsibility |
|---|---|---|
| Profiler | `app/core/profiler.py` | Turn a dataframe into the compact **schema summary** the LLM sees. Raw data never leaves the server. |
| Prompt Builder | `app/core/prompt_builder.py` | Assemble prompts from versioned templates in `prompts/`. |
| LLM Client | `app/llm/` | Provider-agnostic interface; Anthropic impl via direct API calls. Model-per-task routing. |
| Executor | `app/execution/` | **The one pluggable boundary.** `execute(code, data_path)` — subprocess (V1) or Docker (V2) behind one interface. |
| Orchestrator | `app/core/orchestrator.py` | The loop as an explicit state machine. Owns retries, exit conditions, the response contract. |
| Session Store | `app/session/store.py` | Uploaded files + per-session history. In-process for V1. |
| API | `app/api/` | FastAPI: `/upload`, `/ask`, `/health`. |
| Frontend | `frontend/streamlit_app.py` | Upload, chat, render answer + chart + code + self-correction trail. |

## Two load-bearing rules

1. **Schema, not data, to the LLM.** Column names, dtypes, null counts, a few sample
   rows, basic stats. This is how a 2M-row file works with a model that sees a few
   thousand tokens. The generated code runs against the full dataframe locally.
2. **The human stays in the loop.** Every answer ships with the exact code and the
   reasoning. Transparency is both the safety net and the answer to "what if it's wrong?"

## The loop as a state machine

```
PROFILING → GENERATING → EXECUTING → OBSERVING ─┬─→ DONE
   ↑___________CORRECTING ←_____________________┤
                                                 ├─→ NEEDS_CLARIFICATION
                                                 └─→ FAILED
```

Two refinements beyond a naive retry counter (`app/core/orchestrator.py`):
- **Same-error short-circuit** — stop if two consecutive attempts fail identically.
- **Retry vs. ask-the-human** — a `CLARIFY:` result (e.g. the question references a
  non-existent column) surfaces to the user instead of burning the retry budget.

## Phased roadmap

- **V1 (done):** the core loop — upload → ask → answer+chart+code, with self-correction
  and a subprocess sandbox. Streamlit UI.
- **V2:** `DockerExecutor` (no network, capped CPU/mem, ephemeral FS) behind the same
  interface; conversation memory; auto-EDA on upload; Excel + DuckDB/SQL; deploy to a
  public URL with a preloaded sample dataset.
- **V3 (pick 1–2):** ML on request (scikit-learn), forecasting, report export, DB
  connect, cost + caching. Extensions of the engine, not new subsystems.

## Why these choices (and not the alternatives)

- **Monolith, not microservices** — the scope is one loop; service boundaries would
  add ops cost with no benefit.
- **Direct API calls, not LangChain** — a 4-step loop doesn't need an agent framework;
  the abstraction cost would exceed the loop's own complexity. Add one only on real pain.
- **Executor as an interface from day one** — makes the V2 sandbox a config swap, not a
  rewrite, and lets the sandbox be unit-tested without Docker in CI.
- **Streamlit first** — fastest path to a clickable, deployable product. React is a
  V3-optional, justified only if the target role is full-stack.
