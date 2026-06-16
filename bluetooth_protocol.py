import json
import time
from pathlib import Path
from typing import Any


NUS_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
NUS_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
NUS_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

DEFAULT_DATA_DIR = Path("/userdata/student")
DEFAULT_STATUS_FILE = DEFAULT_DATA_DIR / "status.json"
DEFAULT_BLE_RX_FILE = DEFAULT_DATA_DIR / "ble_rx.txt"
DEFAULT_BLE_TASK_FILE = DEFAULT_DATA_DIR / "ble_tasks.jsonl"


def parse_incoming_text(text: str) -> dict[str, Any]:
    """Parse one Bluetooth message into the app's task/command shape."""
    stripped = text.strip()
    if not stripped:
        return {}
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return {"type": "command", "command": stripped}
    if isinstance(value, dict):
        return value
    return {"type": "command", "command": str(value)}


def parse_incoming_bytes(data: bytes) -> dict[str, Any]:
    return parse_incoming_text(data.decode("utf-8", errors="replace"))


def json_line(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")


def hex_bytes(data: bytes) -> str:
    return " ".join(f"{byte:02x}" for byte in data)


def append_ble_rx(text: str, path: Path = DEFAULT_BLE_RX_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(text.strip() + "\n")


def append_ble_task(task: dict[str, Any], path: Path = DEFAULT_BLE_TASK_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(task, ensure_ascii=False) + "\n")


def load_status(path: Path = DEFAULT_STATUS_FILE) -> dict[str, Any]:
    if not path.exists():
        return {"state": "online", "message": "ble uart ready"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"state": "online", "message": f"status read failed: {exc}"}


def status_heartbeat() -> dict[str, Any]:
    status = load_status()
    return {
        "type": "status",
        "state": status.get("state", "online"),
        "message": status.get("message", ""),
        "timestamp": int(time.time()),
    }


def command_reply(command: str) -> dict[str, Any]:
    if command.strip().lower() == "status":
        return {"type": "command_result", "command": "status", "status": load_status()}
    return {"type": "ack", "text": command.strip(), "timestamp": int(time.time())}
