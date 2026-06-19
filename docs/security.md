# Security & isolation model

Running LLM-generated code that touches user data is a genuine security problem. This
document is the honest version — what each phase actually guarantees, and what it does not.

## The threat

The model writes Python that we execute. A bad or adversarial generation could try to:
read secrets from the environment, read/write arbitrary files, exfiltrate data over the
network, or run forever / exhaust resources.

## V1 — subprocess executor (`app/execution/subprocess_executor.py`)

**What it guarantees:**
- **Process isolation** — code runs in a separate OS process; it cannot touch the API
  server's memory, objects, or in-flight requests.
- **Hard wall-clock timeout** — the process is killed past the limit. This stops infinite
  loops and runaway compute. *This is the real boundary in V1.*
- **Scrubbed environment** — the child launches with a minimal env (no API keys or app
  secrets), so generated code can't read them.
- **Confined working directory** — the child runs in a throwaway temp dir.

**What it does NOT guarantee (stated plainly):**
- It is **not** a security sandbox. A subprocess can still read the local filesystem and
  open network sockets.
- The constrained namespace in the runner is a *soft* boundary — Python has escape
  hatches (`__builtins__`, `__class__.__mro__`, …). We do not rely on it for safety.

**Why this is an acceptable V1 answer:** the timeout + process + scrubbed env stop the
most common failure modes (runaway code, secret leakage) and let us prove the engine.
Overclaiming the namespace as "secure" would be the red flag; naming the limit is the
credible move.

## V2 — Docker executor (same interface)

`DockerExecutor` implements the identical `execute(code, data_path)` contract, so the
orchestrator is unchanged. It adds the hard isolation V1 lacks:
- **No network** (`--network none`).
- **Capped CPU and memory** (`--cpus`, `--memory`), killed on breach.
- **Ephemeral, read-only-ish filesystem** — container destroyed after each run; data
  mounted read-only.
- **Non-root user** inside the container.

Switching is a config flip: `AAA_EXECUTOR_BACKEND=docker`.

## V2 — concurrency & resource safety (deploy hardening)

Once it's a public URL, additional limits matter and are cheap to add:
- Max upload size (already enforced: `AAA_MAX_UPLOAD_MB`).
- Cap on concurrent sandboxes / a small request queue, so one user can't starve the host.
- Per-session token budget tracking (V3 cost + caching).

## Residual risks to be ready to discuss

- A correct-looking but **wrong** answer that runs cleanly (no traceback) — mitigated by
  transparency (show the code) and, optionally, result sanity checks / a critique pass.
- Resource exhaustion from a very large upload — mitigated by size caps and (V2) memory caps.
- Prompt injection via crafted column names / data — schema-not-data limits blast radius;
  worth noting as a known consideration.
