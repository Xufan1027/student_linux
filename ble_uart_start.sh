#!/bin/sh
set -eu

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/python/bin/python3}"
RESTART_DELAY="${BLE_RESTART_DELAY:-3}"

if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN=python3
fi

if [ ! -f "$APP_DIR/ble_uart_dbus.py" ]; then
    echo "BLE UART daemon not found: $APP_DIR/ble_uart_dbus.py"
    exit 1
fi

while true; do
    echo "[$(date)] BLE UART advertising starting"
    "$PYTHON_BIN" "$APP_DIR/ble_uart_dbus.py"
    rc=$?
    echo "[$(date)] BLE UART advertising exited rc=$rc, restart after ${RESTART_DELAY}s"
    sleep "$RESTART_DELAY"
done
