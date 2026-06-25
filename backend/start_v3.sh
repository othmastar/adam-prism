#!/usr/bin/env bash
cd /mnt/Workspace/Adam_Prism_Complete_v2/backend
exec /mnt/Workspace/Adam_Prism_Complete_v2/backend/.venv/bin/python -m uvicorn adam_v3.server:app --host 0.0.0.0 --port 8000
