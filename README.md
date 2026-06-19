---
title: DataPilot AI — Autonomous Data Analyst
emoji: 🧭
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🧭 DataPilot AI — Autonomous Data Analyst

**Upload a dataset, ask a question in plain English. An AI agent writes Python, runs it in a sandbox, observes the result, fixes its own errors, and replies with an answer, a chart, and the exact code it ran — so every step is verifiable.**

### ▶️ [**Try the live demo**](https://huggingface.co/spaces/samikshabatra18/datapilot-ai) · 💻 [Source on GitHub](https://github.com/Samikshabatra/datapilot-ai)

> The live app is **bring-your-own-key**: paste a free [Google Gemini API key](https://aistudio.google.com/apikey) in the sidebar — it's used only for your requests and never stored. Then upload a CSV (or use the bundled sample) and ask away.

---

## What makes it more than "an LLM that writes code"

The defensible mechanism is a closed loop, not a one-shot generation:

```
        ┌─────────────────────────────────────────────┐
        │                                             ▼
   ① question + schema → ② LLM writes Python → ③ run in sandbox
        ▲                                             │
        └──────────  ④ observe result / error  ◄──────┘
              (self-correct, up to N times)
                                │
                    ⑤ synthesize an expert answer
```

- **Schema, not data, goes to the LLM.** A profiler sends column names, types, null counts and a few sample rows — so a 2M-row file works against a model that only ever sees a few thousand tokens. The generated code runs against the *full* dataframe locally.
- **It self-corrects.** If the code errors, the traceback is fed back and the agent fixes its own code — stopping early only when it's genuinely stuck (identical retry) or when the question can't be answered from the data (it asks for clarification instead of looping).
- **It always shows its work.** Every answer ships with the code, the reasoning, and the full self-correction trail. Transparency is the safety net.

## Features

- 📊 **Natural-language analytics** on uploaded CSV/Excel — answers, tables, and charts
- 🧠 **ML-engineer proficiency** — picks the right method (regression, statistical tests, forecasting, clustering) using scikit-learn / scipy / statsmodels / seaborn, and interprets the results, caveats and all
- 🔁 **Self-correcting agent loop** with bounded retries and smart exit conditions
- 💬 **Conversation memory** — follow-ups like *"now break that down by region"* resolve in context
- 📋 **One-click EDA** — an instant exploratory overview of any new dataset
- 📓 **Export the session** as a runnable `.ipynb` notebook or `.py` script
- 🔒 **Sandboxed execution** — subprocess (timeout + scrubbed env) or a locked-down Docker container (no network, capped CPU/memory, read-only FS, non-root)
- 🎨 Polished glassmorphic UI

## Architecture

```
Frontend (Streamlit)  →  FastAPI  →  Orchestrator (explicit state machine)
                                       ├─ Profiler        (the schema the LLM sees)
                                       ├─ Prompt Builder  (versioned templates)
                                       ├─ LLM Client      (provider-agnostic: Gemini / Anthropic)
                                       └─ Executor        (interface: subprocess ⇄ Docker)
                                            ↑ the one pluggable boundary
```

The **`Executor` interface** is the key design decision: the orchestrator never knows whether code ran in a subprocess or a Docker container — swapping sandboxes is a config flip, not a rewrite. The reasoning behind the main choices is written up as ADRs in [`docs/decisions/`](docs/decisions/), and the isolation model in [`docs/security.md`](docs/security.md).

## Tech stack

**Python · FastAPI · Streamlit · Google Gemini (provider-agnostic) · pandas / NumPy · scikit-learn / SciPy / statsmodels / seaborn · Docker · pytest**, deployed on **Hugging Face Spaces**.

## Run it locally

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate         # Windows
pip install -e ".[frontend,dev]"

pytest                                                  # tests need no API key (mock LLM + real sandbox)

uvicorn app.main:app --reload --port 8010               # backend
streamlit run ..\frontend\streamlit_app.py              # frontend (separate terminal)
```

Open the Streamlit URL, paste your Gemini key in the sidebar (or set `AAA_GEMINI_API_KEY` in `backend/.env`), upload `sample_data/sales.csv`, and ask *"Which region has the highest total revenue?"*

**Real Docker sandbox (optional):** build the image and flip one config value —
```bash
docker build -t aaa-sandbox:latest -f sandbox/Dockerfile.runner .   # from backend/
# then set AAA_EXECUTOR_BACKEND=docker in backend/.env and restart
```

## A note on the sandbox (stated honestly)

The subprocess executor (used by the public demo) runs code in a separate process with a hard timeout and a scrubbed environment — enough to stop runaway code and keep secrets out of generated code, but **not** a true security boundary. Real isolation — no network, capped CPU/memory, ephemeral filesystem, non-root — is the `DockerExecutor`, which implements the same interface. Naming that limit is deliberate.
