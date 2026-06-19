"""Dataset profiler.

Rule #1 of the whole project: never send raw data to the LLM. We send a compact
*schema summary* — column names, dtypes, null counts, a few sample rows, and basic
numeric stats. This is how a 2M-row file works against a model that only ever sees
a few thousand tokens. The generated code runs against the full dataframe locally.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    null_count: int
    null_pct: float
    n_unique: int
    sample_values: list = field(default_factory=list)
    # numeric-only
    min: float | None = None
    max: float | None = None
    mean: float | None = None


@dataclass
class DatasetProfile:
    n_rows: int
    n_cols: int
    columns: list[ColumnProfile]
    sample_rows_markdown: str

    def to_prompt_block(self) -> str:
        """Render the profile as the compact text block the LLM sees."""
        lines = [f"Dataset shape: {self.n_rows} rows x {self.n_cols} columns", "", "Columns:"]
        for c in self.columns:
            parts = [f"- `{c.name}` ({c.dtype})", f"nulls={c.null_count} ({c.null_pct:.1f}%)", f"unique={c.n_unique}"]
            if c.mean is not None:
                parts.append(f"min={c.min:g} max={c.max:g} mean={c.mean:g}")
            if c.sample_values:
                preview = ", ".join(str(v) for v in c.sample_values[:3])
                parts.append(f"e.g. [{preview}]")
            lines.append("  " + " | ".join(parts))
        lines += ["", "Sample rows:", self.sample_rows_markdown]
        return "\n".join(lines)


def load_dataframe(path: str | Path) -> pd.DataFrame:
    """Load a CSV or Excel file into a dataframe. Tolerant of messy CSVs."""
    p = Path(path)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    # skip_blank_lines + python engine tolerate ragged real-world CSVs
    return pd.read_csv(p, skip_blank_lines=True)


def profile_dataframe(df: pd.DataFrame, sample_rows: int = 5) -> DatasetProfile:
    columns: list[ColumnProfile] = []
    n = len(df)
    for name in df.columns:
        s = df[name]
        nulls = int(s.isna().sum())
        cp = ColumnProfile(
            name=str(name),
            dtype=str(s.dtype),
            null_count=nulls,
            null_pct=(nulls / n * 100) if n else 0.0,
            n_unique=int(s.nunique(dropna=True)),
            sample_values=s.dropna().unique()[:3].tolist(),
        )
        if pd.api.types.is_numeric_dtype(s) and s.notna().any():
            cp.min = float(s.min())
            cp.max = float(s.max())
            cp.mean = float(s.mean())
        columns.append(cp)

    # to_string keeps us free of the optional `tabulate` dependency while still
    # giving the LLM a clean, aligned preview of a few real rows.
    sample = df.head(sample_rows).to_string(index=False)
    return DatasetProfile(
        n_rows=n,
        n_cols=df.shape[1],
        columns=columns,
        sample_rows_markdown=sample,
    )
