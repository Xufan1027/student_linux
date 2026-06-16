#!/bin/sh
set -eu

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/python/bin/python3}"
RESTART_DELAY="${BT_AGENT_RESTART_DELAY:-3}"

if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN=python3
fi

while true; do
    echo "[$(date)] bluetooth pairing agent starting"
    "$PYTHON_BIN" "$APP_DIR/bluetooth_pairing_agent.py"
    rc=$?
    echo "[$(date)] bluetooth pairing agent exited rc=$rc, restart after ${RESTART_DELAY}s"
    sleep "$RESTART_DELAY"
done
