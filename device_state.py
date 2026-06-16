from dataclasses import dataclass, field
from time import time
from typing import Optional


@dataclass
class DeviceState:
    device_id: str
    state: str = "booting"
    message: str = "starting"
    last_task_id: str = ""
    asr_text: str = ""
    ai_text: str = ""
    error: str = ""
    updated_at: float = field(default_factory=time)

    def set_state(self, state: str, message: str = "") -> None:
        self.state = state
        self.message = message
        if state != "error":
            self.error = ""
        self.updated_at = time()

    def set_task(self, task_id: str) -> None:
        self.last_task_id = task_id
        self.updated_at = time()

    def set_result(self, asr_text: str, ai_text: str) -> None:
        self.asr_text = asr_text
        self.ai_text = ai_text
        self.updated_at = time()

    def set_error(self, message: str, task_id: Optional[str] = None) -> None:
        if task_id is not None:
            self.last_task_id = task_id
        self.state = "error"
        self.message = message
        self.error = message
        self.updated_at = time()

    def to_status_payload(self) -> dict:
        return {
            "device_id": self.device_id,
            "state": self.state,
            "message": self.message,
            "last_task_id": self.last_task_id,
            "error": self.error,
            "timestamp": int(self.updated_at),
        }

    def to_result_payload(self, task_id: str, status: str = "ok") -> dict:
        return {
            "device_id": self.device_id,
            "task_id": task_id,
            "asr_text": self.asr_text,
            "ai_text": self.ai_text,
            "status": status,
            "error": self.error,
            "timestamp": int(self.updated_at),
        }
