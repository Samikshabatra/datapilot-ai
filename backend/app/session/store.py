"""Session storage.

V1 decision, made consciously: state lives in an in-process dict, and uploaded
files live on local disk under settings.session_dir. A server restart loses
sessions. That is acceptable for a demo — and being able to say so on purpose
("it's in-process; here's exactly what we'd change for multi-instance") is a
better interview answer than pretending otherwise.

V2 swaps this for a small persistent store (e.g. SQLite/Redis) without touching
callers, since everyone goes through this module.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from ..config import settings
from ..core.profiler import DatasetProfile


@dataclass
class Turn:
    question: str
    answer: str
    code: str


@dataclass
class Session:
    id: str
    data_path: str
    schema_block: str  # cached profiler output — the text the LLM sees
    profile: DatasetProfile
    history: list[Turn] = field(default_factory=list)


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._root = Path(settings.session_dir).resolve()  # absolute: sandbox runs elsewhere
        self._root.mkdir(parents=True, exist_ok=True)

    def create(self, original_filename: str, raw_bytes: bytes) -> str:
        sid = uuid.uuid4().hex
        suffix = Path(original_filename).suffix or ".csv"
        path = self._root / f"{sid}{suffix}"
        path.write_bytes(raw_bytes)
        # profile lazily-imported to keep this module light
        from ..core.profiler import load_dataframe, profile_dataframe

        df = load_dataframe(path)
        profile = profile_dataframe(df, sample_rows=settings.sample_rows)
        self._sessions[sid] = Session(
            id=sid,
            data_path=str(path),
            schema_block=profile.to_prompt_block(),
            profile=profile,
        )
        return sid

    def get(self, sid: str) -> Session:
        if sid not in self._sessions:
            raise KeyError(f"Unknown session id: {sid}")
        return self._sessions[sid]

    def add_turn(self, sid: str, turn: Turn) -> None:
        self.get(sid).history.append(turn)


# Single process-wide store for V1.
store = SessionStore()
