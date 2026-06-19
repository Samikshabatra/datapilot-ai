"""The script that runs INSIDE the sandbox (subprocess in V1, container in V2).

It is intentionally self-contained and imports nothing from the app package, so the
same file can be copied into a Docker image unchanged. Contract:

    python runner.py <payload_json_path> <result_json_path>

payload  = {"code": <str>, "data_path": <str>}
result   = ExecutionResult-shaped JSON written to <result_json_path>

It loads the dataframe, executes the user code with a constrained namespace,
captures stdout, the `result` variable, and any matplotlib figure, and serializes
everything. User-code exceptions are caught and returned as `error` (a traceback)
so the parent loop can self-correct — they are NOT propagated as process failures.

NOTE (honest about limits): a restricted namespace is a *soft* boundary, not real
isolation — Python has escape hatches. The hard boundary is the OS-level timeout
in V1 and the Docker container (no network, capped CPU/mem, ephemeral FS) in V2.
"""
from __future__ import annotations

import base64
import io
import json
import sys
import traceback
from contextlib import redirect_stdout

MAX_REPR = 20_000


def _capture_figure() -> str | None:
    try:
        import matplotlib.pyplot as plt

        if plt.get_fignums():
            buf = io.BytesIO()
            plt.gcf().savefig(buf, format="png", bbox_inches="tight", dpi=110)
            plt.close("all")
            return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        pass
    return None


def run(payload: dict) -> dict:
    import matplotlib

    matplotlib.use("Agg")  # headless backend, no display required
    import matplotlib.pyplot as plt  # noqa: F401
    import numpy as np
    import pandas as pd

    out: dict = {"ok": False, "stdout": "", "result_repr": "", "error": None,
                 "chart_png_base64": None, "result_kind": "scalar", "result_table": None}

    try:
        df = pd.read_excel(payload["data_path"]) if payload["data_path"].lower().endswith(
            (".xlsx", ".xls")
        ) else pd.read_csv(payload["data_path"], skip_blank_lines=True)
    except Exception:
        out["error"] = "Failed to load dataset:\n" + traceback.format_exc()
        return out

    namespace = {"df": df, "pd": pd, "np": np, "plt": plt, "__name__": "__sandbox__"}
    stdout_buf = io.StringIO()
    try:
        with redirect_stdout(stdout_buf):
            exec(payload["code"], namespace)  # noqa: S102 — this is the sandbox's job
        result = namespace.get("result", None)
        out["ok"] = True
        out["result_repr"] = ("" if result is None else repr(result))[:MAX_REPR]
        # Capture tabular results structurally so the UI can render a real table
        # instead of a run-on repr. Cap rows so a huge result can't bloat the payload.
        table = None
        if isinstance(result, pd.DataFrame):
            table = result.head(200)
        elif isinstance(result, pd.Series):
            table = result.head(200).to_frame()
        if table is not None:
            out["result_kind"] = "dataframe"
            out["result_table"] = table.to_json(orient="split", date_format="iso")
    except Exception:
        out["error"] = traceback.format_exc()
    finally:
        out["stdout"] = stdout_buf.getvalue()[:MAX_REPR]
        out["chart_png_base64"] = _capture_figure()
    return out


if __name__ == "__main__":
    payload_path, result_path = sys.argv[1], sys.argv[2]
    with open(payload_path, encoding="utf-8") as f:
        payload = json.load(f)
    result = run(payload)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
