"""Central configuration. Everything tunable lives here and is overridable via env."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AAA_", extra="ignore")

    # --- LLM ---
    # Provider is swappable behind the LLMClient interface: "gemini" | "anthropic".
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    # Model-per-task routing: a strong model for code generation, a cheaper/faster
    # one for the self-correction retries. This is the "cost per task" story.
    # Defaults below are Gemini models; override per provider via env.
    # NOTE: free-tier daily caps are PER MODEL and small (~20 req/day for
    # gemini-2.5-flash, similar for 2.0-flash). flash-lite has the most headroom,
    # so it's the default. On a paid tier, switch to gemini-2.5-flash / -pro here.
    model_generate: str = "gemini-2.5-flash-lite"
    model_correct: str = "gemini-2.5-flash-lite"
    # Each question costs 2 calls (code-gen + answer synthesis). On a tight free
    # quota, set this false to halve usage — you lose the expert narrative and get
    # the raw computed result instead.
    synthesize_answers: bool = True
    # Gemini 2.5 are "thinking" models — they spend output tokens on internal
    # reasoning before emitting text, so the cap must be generous enough to cover
    # thinking + the actual code, or you get an empty/truncated response.
    max_tokens: int = 8192

    # --- The loop ---
    max_retries: int = 3  # self-correction attempts before giving up gracefully

    # --- Execution sandbox ---
    execution_timeout_s: int = 30  # hard wall-clock cap on generated code
    max_output_chars: int = 20_000  # truncate stdout/results fed back to the model
    executor_backend: str = "subprocess"  # "subprocess" (V1) | "docker" (V2)
    # Docker sandbox (used when executor_backend == "docker")
    docker_image: str = "aaa-sandbox:latest"  # built from sandbox/Dockerfile.runner
    docker_memory: str = "512m"  # hard memory cap; container killed on breach
    docker_cpus: str = "1.0"  # CPU cap
    docker_pids_limit: int = 256  # fork-bomb guard

    # --- Upload / profiling ---
    max_upload_mb: int = 100
    sample_rows: int = 5  # rows shown to the LLM in the schema summary

    # --- Storage ---
    session_dir: str = ".sessions"  # where uploaded files + state live (per-process)


settings = Settings()
