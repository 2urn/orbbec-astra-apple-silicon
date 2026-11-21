#!/bin/bash
# Sends the Astra to Resolume, TouchDesigner, MadMapper, VDMX, OBS... as Syphon sources.
# Keep this window open while you use it. Close it (or press Ctrl+C) to stop.
cd "$(dirname "$0")/tools" || exit 1
[ -x ../.venv/bin/python ] || { echo "Run 'Setup (run first).command' first."; read -n 1 -s -r; exit 1; }
../.venv/bin/python syphon_out.py "$@"
