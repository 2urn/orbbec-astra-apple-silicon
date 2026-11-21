#!/bin/bash
# Double-click me once. Builds the driver and installs the Python tools (5-10 minutes).
cd "$(dirname "$0")" || exit 1
echo "=== Astra for Apple Silicon: setup ==="
if ! xcode-select -p >/dev/null 2>&1; then
  echo "Apple's free developer tools are needed. A window will pop up - click Install,"
  echo "wait for it to finish, then double-click this file again."
  xcode-select --install
  read -n 1 -s -r -p "Press any key to close."; exit 1
fi
./build.sh || { read -n 1 -s -r -p "Setup failed (see above). Press any key to close."; exit 1; }
echo "==> Installing Python tools"
python3 -m venv .venv && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -r requirements.txt \
  || { read -n 1 -s -r -p "Python setup failed (see above). Press any key to close."; exit 1; }
echo
echo "All set! Plug in your Astra, then double-click:"
echo "  'Astra Viewer'               to see the camera"
echo "  'Astra to Syphon.command'    to use it in Resolume / TouchDesigner / MadMapper"
echo "  'Astra Web Bridge.command'   to stream it to browser apps"
read -n 1 -s -r -p "Press any key to close."
