#!/usr/bin/env bash
# Launch the FastAPI backend (internal :8000), wait for it, then start the
# Streamlit UI on the public port (:7860). One container, two processes.
set -e

cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Wait until the backend answers /health (max ~40s) before starting the UI.
python - <<'PY'
import time, urllib.request
for _ in range(40):
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1)
        print("backend ready"); break
    except Exception:
        time.sleep(1)
PY

cd /app
exec streamlit run frontend/streamlit_app.py --server.port 7860 --server.address 0.0.0.0
