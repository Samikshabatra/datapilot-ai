"""Assembles prompts from versioned template files + runtime context.

Templates live in backend/prompts/ as .md files so they can be iterated on and
diffed independently of code. The builder injects the schema summary, the question,
and (for correction) the failing code and traceback.
"""
from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def _template(name: str) -> str:
    # Read fresh each call (not cached): prompt files are tiny, and this lets prompt
    # edits take effect without a process restart — important while iterating.
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _fill(template: str, **fields: str) -> str:
    """Substitute only our named {tokens}. Deliberately NOT str.format(): prompt
    templates contain literal braces in code examples (e.g. f-strings), which
    str.format would misread as fields. Inserted values are placed literally, so
    braces in the data can't break or re-trigger substitution."""
    out = template
    for key, value in fields.items():
        out = out.replace("{" + key + "}", value)
    return out


def build_generate_prompt(schema: str, question: str, history: str = "") -> str:
    return _fill(_template("generate_code.md"), schema=schema, question=question, history=history)


def build_correction_prompt(schema: str, question: str, previous_code: str, error: str) -> str:
    return _fill(
        _template("self_correct.md"),
        schema=schema, question=question, previous_code=previous_code, error=error,
    )


def build_synthesis_prompt(question: str, code: str, stdout: str, result: str) -> str:
    return _fill(
        _template("synthesize_answer.md"),
        question=question, code=code,
        stdout=stdout or "(no printed output)", result=result or "(none)",
    )


def render_history(turns: list, max_turns: int = 4) -> str:
    """Format recent conversation turns for the generation prompt so follow-up
    questions ('now break that down by region') resolve against prior context.
    Bounded to the last `max_turns` to control token cost."""
    if not turns:
        return ""
    recent = turns[-max_turns:]
    lines = ["", "## Conversation so far (most recent last)"]
    for i, t in enumerate(recent, 1):
        lines.append(f"{i}. Q: {t.question}")
        lines.append(f"   A: {t.answer[:400]}")
    lines.append("")
    return "\n".join(lines)


def build_eda_prompt(schema: str) -> str:
    # V2: reuses the engine for auto-EDA on upload.
    return _fill(_template("eda_profile.md"), schema=schema)
