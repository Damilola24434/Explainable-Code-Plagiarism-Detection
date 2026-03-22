#!/bin/sh
set -e

export PYTHONPATH=/app:$PYTHONPATH
cd /app
python scripts/db/create_tables.py
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
