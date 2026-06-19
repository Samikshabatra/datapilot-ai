# Single-container deploy for Hugging Face Spaces (Docker SDK).
# Runs the FastAPI backend internally on :8000 and the Streamlit UI on :7860
# (the port HF exposes). Uses the subprocess sandbox — no Docker-in-Docker needed.
FROM python:3.11-slim

# Runtime lib needed by scipy / scikit-learn wheels.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces convention: run as non-root uid 1000 with a writable HOME.
RUN useradd -m -u 1000 user
ENV HOME=/home/user

WORKDIR /app

# Python deps (backend + frontend extras). Copy backend first for layer caching.
COPY --chown=user backend /app/backend
RUN pip install --no-cache-dir "/app/backend[frontend]"

# App code + a sample dataset so visitors can try it instantly.
COPY --chown=user frontend /app/frontend
COPY --chown=user sample_data /app/sample_data
COPY --chown=user start.sh /app/start.sh

# Runtime configuration. NOTE: no .env here — the Gemini key comes from an HF
# Space *secret* (AAA_GEMINI_API_KEY) injected as an env var at runtime.
ENV AAA_API_BASE=http://127.0.0.1:8000 \
    AAA_EXECUTOR_BACKEND=subprocess \
    AAA_SESSION_DIR=/home/user/.sessions \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/home/user/.mpl \
    STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

USER user
RUN mkdir -p /home/user/.sessions /home/user/.mpl

EXPOSE 7860
CMD ["bash", "/app/start.sh"]
