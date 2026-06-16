#!/bin/sh
set -eu

cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-/opt/python/bin/python3}"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN=python3
fi
exec "$PYTHON_BIN" main.py
