#!/bin/sh
set -eu

trap 'kill 0' INT TERM EXIT
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
npm run dev -- --port 5173 &
wait
