"""Executor tests — the sandbox must capture results, errors, charts, and timeouts
without ever raising into the caller."""
from __future__ import annotations

from app.execution.subprocess_executor import SubprocessExecutor


def test_returns_result(sample_csv):
    ex = SubprocessExecutor(timeout_s=15)
    r = ex.execute("result = int(df['revenue'].sum())", sample_csv)
    assert r.ok
    assert r.result_repr == "875"


def test_captures_error_as_traceback(sample_csv):
    ex = SubprocessExecutor(timeout_s=15)
    r = ex.execute("result = df['does_not_exist'].sum()", sample_csv)
    assert not r.ok
    assert "KeyError" in (r.error or "")


def test_timeout_is_enforced(sample_csv):
    ex = SubprocessExecutor(timeout_s=2)
    r = ex.execute("while True:\n    pass", sample_csv)
    assert not r.ok
    assert r.timed_out


def test_captures_chart(sample_csv):
    ex = SubprocessExecutor(timeout_s=15)
    r = ex.execute("df['revenue'].plot(kind='bar')\nresult = 'plotted'", sample_csv)
    assert r.ok
    assert r.chart_png_base64 is not None


def test_captures_stdout(sample_csv):
    ex = SubprocessExecutor(timeout_s=15)
    r = ex.execute("print('hello from sandbox')\nresult = 1", sample_csv)
    assert "hello from sandbox" in r.stdout
