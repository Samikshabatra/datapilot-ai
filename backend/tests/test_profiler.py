from __future__ import annotations

from app.core.profiler import load_dataframe, profile_dataframe


def test_profile_has_columns_and_stats(sample_csv):
    df = load_dataframe(sample_csv)
    p = profile_dataframe(df, sample_rows=3)
    assert p.n_rows == 5
    assert p.n_cols == 3
    names = {c.name for c in p.columns}
    assert names == {"region", "revenue", "units"}
    revenue = next(c for c in p.columns if c.name == "revenue")
    assert revenue.mean is not None
    block = p.to_prompt_block()
    assert "revenue" in block and "Sample rows:" in block
