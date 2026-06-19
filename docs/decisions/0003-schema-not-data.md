# ADR 0003 — Send the schema to the LLM, never the raw data

**Status:** accepted (V1)

## Context
Datasets can be millions of rows. Models see a few thousand tokens. Stuffing data into
the prompt is impossible at scale and leaks all of it to the provider.

## Decision
The profiler computes a compact **schema summary** — column names, dtypes, null counts,
unique counts, basic numeric stats, and 3–5 sample rows. Only this summary goes to the
LLM. Generated code runs against the full dataframe locally in the sandbox.

## Consequences
- Dataset size is decoupled from prompt size — a 2M-row file costs the same prompt as a
  200-row file.
- Less data exposure to the model provider (only a handful of sample values).
- The profiler is a first-class component, not a helper.
- Trade-off: the model reasons from a summary, so questions that hinge on specific unseen
  values may need a clarifying round — handled by the retry-vs-clarify path.
