# ADR 0002 — Direct API calls, no agent framework (yet)

**Status:** accepted (V1)

## Context
LangChain / LlamaIndex are the default reach for "LLM that does things." The roadmap
advises adding them only "if you feel real pain without it."

## Decision
Use the Anthropic SDK directly behind a thin provider-agnostic `LLMClient` interface.
The orchestrator owns the loop explicitly as a state machine.

## Rationale
- The loop is 4 steps. A framework's control-flow abstractions would be larger than the
  loop they'd wrap, and harder to debug when self-correction misbehaves.
- An explicit state machine gives precise control over retry caps, the same-error
  short-circuit, and the retry-vs-clarify decision — logic that frameworks obscure.
- The `LLMClient` interface keeps the door open: a framework can be slotted in later as
  another implementation if real pain appears (e.g. complex multi-tool routing).

## Consequences
- Full visibility and control over tokens, models per task, and prompts.
- We write the loop ourselves (small, already done and tested).
