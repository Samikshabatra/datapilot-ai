"""V1 frontend — the fastest path to clickable.

Upload a dataset, ask questions, and see the transparent triple: the answer, the
chart, and the exact code that ran — plus the full self-correction trail when the
agent had to fix its own mistakes.

    streamlit run frontend/streamlit_app.py

Set API_BASE if the backend isn't on localhost:8000.
"""
from __future__ import annotations

import base64
import io
import json
import os

import pandas as pd
import requests
import streamlit as st

import theme

# This project standardises on port 8010 for the backend. (Port 8000 is commonly
# held by Docker/WSL port-forwards on this machine and can't always be freed
# cleanly.) Override with AAA_API_BASE if your backend runs elsewhere.
API_BASE = os.environ.get("AAA_API_BASE", "http://localhost:8010")

st.set_page_config(page_title="DataPilot AI · Autonomous Data Analyst",
                   page_icon="🧭", layout="wide")
theme.apply_theme()
theme.render_header()


def _render_chart(b64: str | None):
    if b64:
        st.image(base64.b64decode(b64))


def _render_answer(answer: str, result_kind: str, result_table: str | None):
    """Show the expert narrative answer, plus the supporting table when present."""
    if answer:
        st.markdown(answer)
    if result_kind == "dataframe" and result_table:
        try:
            st.dataframe(pd.read_json(io.StringIO(result_table), orient="split"))
        except Exception:
            pass  # narrative already shown; table is supplementary


_EXPORT_HEADER = [
    "Autonomous Data Analyst — exported session.",
    "",
    "This bundles the code the agent generated for each question, in order.",
    "Set DATA_PATH to your dataset and run top to bottom.",
]
_EXPORT_IMPORTS = (
    "import pandas as pd\n"
    "import numpy as np\n"
    "import matplotlib.pyplot as plt\n"
    "# Also available where the agent used them: scikit-learn, scipy, statsmodels, seaborn\n"
    "\n"
    'DATA_PATH = "your_dataset.csv"  # <-- point this at your file\n'
    "df = pd.read_csv(DATA_PATH)"
)


def build_python_script(chat: list) -> str:
    """Compile the session's code into one runnable .py script."""
    parts = ['"""' + "\n".join(_EXPORT_HEADER) + '"""', "", _EXPORT_IMPORTS, ""]
    for i, turn in enumerate(chat, 1):
        parts.append("# " + "=" * 70)
        parts.append(f"# Q{i}: {turn['q']}")
        answer = (turn.get("answer") or "").strip()
        if answer:
            parts.append("#")
            parts.extend("# " + line for line in answer.splitlines())
        parts.append("# " + "=" * 70)
        parts.append((turn.get("code") or "").strip())
        parts.append("print(result)  # show this question's result")
        parts.append("")
    return "\n".join(parts)


def _nb_cell(cell_type: str, source: str) -> dict:
    cell = {"cell_type": cell_type, "metadata": {}, "source": source}
    if cell_type == "code":
        cell.update(execution_count=None, outputs=[])
    return cell


def build_notebook(chat: list) -> str:
    """Compile the session into a runnable Jupyter notebook (.ipynb JSON)."""
    cells = [
        _nb_cell("markdown", "# Autonomous Data Analyst — exported session\n\n"
                 "Set `DATA_PATH` to your dataset, then run the cells top to bottom."),
        _nb_cell("code", "%matplotlib inline\n" + _EXPORT_IMPORTS + "\ndf.head()"),
    ]
    for i, turn in enumerate(chat, 1):
        cells.append(_nb_cell("markdown", f"## Q{i}: {turn['q']}\n\n{turn.get('answer', '')}"))
        cells.append(_nb_cell("code", (turn.get("code") or "").strip() + "\n\nresult"))
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(nb, indent=1)


def _auth_headers() -> dict:
    """Send the visitor's own API key with each analysis request (BYOK).
    The key is held only in this browser session and never stored server-side."""
    key = st.session_state.get("api_key", "")
    return {"X-LLM-Key": key} if key else {}


# --- API key (BYOK) ---
with st.sidebar:
    st.header("🔑 API key")
    st.session_state["api_key"] = st.text_input(
        "Gemini API key", type="password", value=st.session_state.get("api_key", ""),
        help="Your key is sent only with your own requests and is never stored. "
             "Get a free key at aistudio.google.com/apikey",
        placeholder="AIza…",
    )
    if not st.session_state.get("api_key"):
        st.caption("⚠ Enter your Gemini key to ask questions.")

# --- Upload ---
with st.sidebar:
    st.header("1 · Dataset")
    file = st.file_uploader("CSV or Excel", type=["csv", "xlsx", "xls"])
    if file and st.button("Upload & profile", use_container_width=True):
        resp = requests.post(f"{API_BASE}/upload", files={"file": (file.name, file.getvalue())})
        if resp.ok:
            data = resp.json()
            st.session_state["session_id"] = data["session_id"]
            st.session_state["schema_preview"] = data["schema_preview"]
            st.session_state["chat"] = []
            st.session_state.pop("eda", None)          # clear any prior overview
            st.success(f"Loaded {data['n_rows']} rows × {data['n_cols']} cols")
        else:
            st.error(resp.text)

    if "schema_preview" in st.session_state:
        with st.expander("What the agent sees (schema, not data)"):
            st.code(st.session_state["schema_preview"], language="text")

# --- Ask ---
if "session_id" not in st.session_state:
    st.info("⬅ Upload a dataset to begin.")
    st.stop()

# --- Optional EDA: on demand, not automatic ---
if st.button("📋 Generate dataset overview (optional)"):
    with st.spinner("Profiling your dataset — distributions, missingness, correlations…"):
        try:
            er = requests.get(f"{API_BASE}/eda/{st.session_state['session_id']}",
                              headers=_auth_headers(), timeout=180)
            st.session_state["eda"] = er.json() if er.ok else {"state": "failed", "error": er.text}
        except Exception as e:
            st.session_state["eda"] = {"state": "failed", "error": str(e)}

if "eda" in st.session_state:
    eda = st.session_state["eda"]
    with st.expander("📋 Dataset overview", expanded=True):
        if eda.get("state") == "done":
            _render_answer(eda.get("answer", ""), eda.get("result_kind", "scalar"), eda.get("result_table"))
            _render_chart(eda.get("chart_png_base64"))
            with st.expander("Show the EDA code that ran"):
                st.code(eda.get("code", ""), language="python")
        else:
            st.warning(f"Couldn't profile this dataset: {eda.get('error', 'unknown error')}")

st.header("2 · Ask a question")
for turn in st.session_state.get("chat", []):
    with st.chat_message("user"):
        st.write(turn["q"])
    with st.chat_message("assistant"):
        _render_answer(turn["answer"], turn.get("result_kind", "scalar"), turn.get("result_table"))
        _render_chart(turn.get("chart"))
        with st.expander("Show the code that ran"):
            st.code(turn["code"], language="python")

question = st.chat_input("e.g. Which region had the highest average revenue?")
if question:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"), st.spinner("Writing code, executing, observing…"):
        resp = requests.post(
            f"{API_BASE}/ask",
            headers=_auth_headers(),
            json={"session_id": st.session_state["session_id"], "question": question},
        )
        if not resp.ok:
            st.error(resp.text)
            st.stop()
        r = resp.json()
        state = r["state"]

        if state == "done":
            _render_answer(r["answer"], r.get("result_kind", "scalar"), r.get("result_table"))
            _render_chart(r.get("chart_png_base64"))
            if r.get("reasoning"):
                st.caption(f"💭 {r['reasoning']}")
            with st.expander("Show the code that ran"):
                st.code(r["code"], language="python")
            n = len(r["attempts"])
            if n > 1:
                st.caption(f"🔁 Self-corrected — solved on attempt {n}.")
                with st.expander("See the self-correction trail"):
                    for a in r["attempts"]:
                        tag = "✅" if a["error"] is None else "❌"
                        st.markdown(f"{tag} **Attempt {a['index'] + 1}**")
                        st.code(a["code"], language="python")
                        if a["error"]:
                            st.code(a["error"], language="text")
            st.session_state["chat"].append(
                {"q": question, "answer": r["answer"], "code": r["code"],
                 "chart": r.get("chart_png_base64"),
                 "result_kind": r.get("result_kind", "scalar"),
                 "result_table": r.get("result_table")}
            )
        elif state == "needs_clarification":
            st.warning(f"🤔 The agent needs clarification: {r['error']}")
        else:
            st.error(f"The agent could not solve this after retries.\n\n{r.get('error', '')}")
            if r.get("attempts"):
                with st.expander("See what it tried"):
                    for a in r["attempts"]:
                        st.code(a["code"], language="python")
                        if a["error"]:
                            st.code(a["error"], language="text")

# --- Export the whole session's code (built client-side; no API/LLM call) ---
# Rendered last so it includes the question just asked this run.
_chat = st.session_state.get("chat", [])
with st.sidebar:
    st.divider()
    st.header("2 · Export code")
    if _chat:
        st.caption(f"{len(_chat)} question(s) in this session.")
        st.download_button(
            "⬇ Download notebook (.ipynb)", build_notebook(_chat),
            file_name="analysis_session.ipynb", mime="application/x-ipynb+json",
            use_container_width=True,
        )
        st.download_button(
            "⬇ Download script (.py)", build_python_script(_chat),
            file_name="analysis_session.py", mime="text/x-python",
            use_container_width=True,
        )
    else:
        st.caption("Ask a question to enable code export.")
