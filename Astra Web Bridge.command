#!/bin/bash
# Streams the Astra's depth + colour to browser apps on this Mac (ws://localhost:8766).
# Keep this window open while you use it. Close it (or press Ctrl+C) to stop.
cd "$(dirname "$0")/tools" || exit 1
[ -x ../.venv/bin/python ] || { echo "Run 'Setup (run first).command' first."; read -n 1 -s -r; exit 1; }
../.venv/bin/python -c "import websockets" 2>/dev/null || ../.venv/bin/pip install -q websockets
../.venv/bin/python web_bridge.py "$@"
