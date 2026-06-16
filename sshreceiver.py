import argparse
import json
import sys
from pathlib import Path

from bluetooth_protocol import DEFAULT_BLE_TASK_FILE, append_ble_task


def parse_payload(raw: str) -> dict:
    stripped = raw.strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return {"type": "command", "command": stripped}
    if isinstance(value, dict):
        return value
    return {"type": "command", "command": str(value)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Receive one task/command over SSH and echo it back.")
    parser.add_argument("payload", nargs="?", help="JSON task or plain text command. Reads stdin if omitted.")
    parser.add_argument("--task-file", default=str(DEFAULT_BLE_TASK_FILE), help="Shared task queue file main.py polls.")
    parser.add_argument("--no-enqueue", action="store_true", help="Only echo, do not write into the task queue.")
    args = parser.parse_args()

    raw = args.payload if args.payload is not None else sys.stdin.read()
    if not raw or not raw.strip():
        print(json.dumps({"error": "empty payload"}, ensure_ascii=False))
        return 1

    payload = parse_payload(raw)

    if not args.no_enqueue:
        append_ble_task(payload, path=Path(args.task_file))

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
