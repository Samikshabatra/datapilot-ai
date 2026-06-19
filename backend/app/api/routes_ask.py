"""POST /ask — run the core loop for one question against an uploaded dataset.
Returns the full transparent payload: answer, code, reasoning, chart, and every
self-correction attempt."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ..core import prompt_builder as pb
from ..core.orchestrator import Orchestrator
from ..core.response import AgentResponse
from ..session.store import Turn, store
from .deps import build_orchestrator

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    session_id: str
    question: str


@router.post("/ask", response_model=AgentResponse)
def ask(req: AskRequest, x_llm_key: str | None = Header(default=None)) -> AgentResponse:
    try:
        sess = store.get(req.session_id)
    except KeyError:
        raise HTTPException(404, "Unknown session_id — upload a dataset first.")

    if not req.question.strip():
        raise HTTPException(400, "Question must not be empty.")

    try:
        orch: Orchestrator = build_orchestrator(x_llm_key)
    except ValueError as e:  # no key supplied and none configured on the server
        raise HTTPException(503, f"Agent is not configured: {e}") from e
    history = pb.render_history(sess.history)
    response = orch.run(
        schema=sess.schema_block,
        question=req.question,
        data_path=sess.data_path,
        history=history,
    )

    if response.succeeded:
        store.add_turn(
            req.session_id,
            Turn(question=req.question, answer=response.answer, code=response.code),
        )
    return response
