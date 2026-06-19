"""GET /eda/{session_id} — auto exploratory data analysis.

Reuses the same engine (generate -> sandbox -> self-correct -> synthesize) as a
normal question, driven by a canned EDA brief. Returns the standard AgentResponse:
an expert written overview, a multi-panel chart, and the exact code that produced
it. Does NOT touch conversation history — it's a profile, not a user turn.
"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from ..core.orchestrator import Orchestrator
from ..core.response import AgentResponse
from ..session.store import store
from .deps import build_orchestrator

router = APIRouter(tags=["eda"])

# A fixed analyst brief. Kept deliberately SIMPLE and robust — an over-ambitious
# brief makes the model write complex, error-prone code. Single figure with a
# couple of panels matches the sandbox's one-figure capture.
EDA_BRIEF = (
    "Give a brief exploratory overview of this dataset for a first-time viewer. "
    "Keep the code SIMPLE and robust — avoid deeply nested expressions. Compute: "
    "the row/column count, the count and percentage of missing values per column, "
    "and which columns look constant or duplicated. Build ONE matplotlib figure "
    "with at most TWO subplots, for example a bar chart of missing values per "
    "column and either a histogram of one key numeric column or a bar chart of the "
    "value counts of one key categorical column. Assign a small dict of the key "
    "findings (shape, top missing columns, any flags) to `result`. Do not attempt a "
    "correlation heatmap or per-column loops that build long strings."
)


@router.get("/eda/{session_id}", response_model=AgentResponse)
def eda(session_id: str, x_llm_key: str | None = Header(default=None)) -> AgentResponse:
    try:
        sess = store.get(session_id)
    except KeyError:
        raise HTTPException(404, "Unknown session_id — upload a dataset first.")

    try:
        orch: Orchestrator = build_orchestrator(x_llm_key)
    except ValueError as e:
        raise HTTPException(503, f"Agent is not configured: {e}") from e

    return orch.run(schema=sess.schema_block, question=EDA_BRIEF, data_path=sess.data_path)
