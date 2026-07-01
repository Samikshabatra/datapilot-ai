from __future__ import annotations

from app.core.prompt_builder import _fill, render_history


def test_fill_substitutes_named_tokens():
    template = "Schema:\n{schema}\n\nQuestion: {question}"
    out = _fill(template, schema="col_a, col_b", question="what is the mean?")
    assert out == "Schema:\ncol_a, col_b\n\nQuestion: what is the mean?"


def test_fill_ignores_literal_braces_in_template():
    # Regression test: templates can contain code examples with literal braces
    # (e.g. an f-string like f"{value:.2f}"). str.format() would raise KeyError
    # on these; _fill must leave them untouched since they aren't named fields.
    template = 'Example code: f"{value:.2f}"\n\nQuestion: {question}'
    out = _fill(template, question="why did revenue drop?")
    assert out == 'Example code: f"{value:.2f}"\n\nQuestion: why did revenue drop?'


def test_fill_ignores_literal_braces_in_substituted_values():
    # Inserted values are placed literally, so braces inside the data itself
    # can't be mistaken for further tokens or trigger re-substitution.
    template = "Result: {result}"
    out = _fill(template, result="{'a': 1}")
    assert out == "Result: {'a': 1}"


def test_render_history_empty():
    assert render_history([]) == ""


def test_render_history_bounds_to_max_turns():
    class Turn:
        def __init__(self, q, a):
            self.question = q
            self.answer = a

    turns = [Turn(f"q{i}", f"a{i}") for i in range(6)]
    out = render_history(turns, max_turns=4)
    assert "q0" not in out and "q1" not in out
    assert "q2" in out and "q5" in out
