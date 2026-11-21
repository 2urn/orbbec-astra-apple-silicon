#!/bin/bash
# Live depth + colour viewer. Keys: 1-9 change views, Esc to quit.
cd "$(dirname "$0")/dist" || exit 1
[ -x ./NiViewer ] || { echo "Run 'Setup (run first).command' first."; read -n 1 -s -r; exit 1; }
./NiViewer
