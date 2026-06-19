"""POST /upload — accept a CSV/Excel file, profile it, return a session id + the
schema summary the agent will work from. The raw data never leaves the server."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..config import settings
from ..session.store import store

router = APIRouter(tags=["upload"])


class ColumnOut(BaseModel):
    name: str
    dtype: str
    null_pct: float
    n_unique: int


class UploadResponse(BaseModel):
    session_id: str
    n_rows: int
    n_cols: int
    columns: list[ColumnOut]
    schema_preview: str


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(400, "Please upload a .csv, .xlsx, or .xls file.")

    raw = await file.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds the {settings.max_upload_mb} MB limit.")

    try:
        sid = store.create(file.filename, raw)
    except Exception as e:  # malformed file, unreadable, etc.
        raise HTTPException(422, f"Could not read the dataset: {e}") from e

    sess = store.get(sid)
    p = sess.profile
    return UploadResponse(
        session_id=sid,
        n_rows=p.n_rows,
        n_cols=p.n_cols,
        columns=[
            ColumnOut(name=c.name, dtype=c.dtype, null_pct=round(c.null_pct, 1), n_unique=c.n_unique)
            for c in p.columns
        ],
        schema_preview=sess.schema_block,
    )
