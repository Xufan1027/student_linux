import argparse
import copy
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from audio_play import play_audio
from audio_record import record_wav
from device_state import DeviceState
from display import show_error, show_result, show_status, show_task
from mqtt_client import StudentMqttClient
from ws_client import AgentResponseError, WsClient
from web_server import start_web_server


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def runtime_dir(config: dict) -> Path:
    storage = config.get("storage", {})
    base_dir = Path(storage.get("data_dir", "/userdata/student"))
    work_dir = Path(config["audio"].get("work_dir", "runtime"))
    if not work_dir.is_absolute():
        work_dir = base_dir / work_dir
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


def storage_path(config: dict, key: str, default_name: str) -> Path:
    storage = config.get("storage", {})
    base_dir = Path(storage.get("data_dir", "/userdata/student"))
    base_dir.mkdir(parents=True, exist_ok=True)
    path = Path(storage.get(key, str(base_dir / default_name)))
    if not path.is_absolute():
        path = base_dir / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_env_check() -> int:
    commands = [
        ["uname", "-a"],
        ["cat", "/etc/os-release"],
        ["python3", "--version"],
        ["which", "python3"],
        ["arecord", "-l"],
        ["aplay", "-l"],
        ["ip", "addr"],
    ]
    for cmd in commands:
        print(f"\n$ {' '.join(cmd)}", flush=True)
        try:
            subprocess.run(cmd, check=False)
        except FileNotFoundError as exc:
            print(f"command not found: {exc.filename}", flush=True)
    return 0


class StudentApp:
    def __init__(self, config: dict, transport: str = "none"):
        self.config = config
        self.state = DeviceState(device_id=config["device"]["device_id"])
        self.ws = WsClient(config)
        self.transport = transport
        self.mqtt: Optional[StudentMqttClient] = None
        self.tasks: "queue.Queue[dict]" = queue.Queue()
        self.file_mode = False
        self.data_dir = Path(config.get("storage", {}).get("data_dir", "/userdata/student"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = storage_path(config, "status_file", "status.json")
        self.results_file = storage_path(config, "results_file", "results.jsonl")
        self.last_record_file = storage_path(config, "last_record_file", "last_record.wav")
        self.sample_audio = storage_path(config, "sample_audio", "sample.wav")
        self.ble_task_file = self.data_dir / "ble_tasks.jsonl"
        if transport == "mqtt":
            self.mqtt = StudentMqttClient(config, on_task=self.enqueue_task)

    def enqueue_task(self, task: dict) -> None:
        self.tasks.put(task)

    def publish_status(self, state: str, message: str = "") -> None:
        self.state.set_state(state, message)
        payload = self.state.to_status_payload()
        self.write_status(payload)
        show_status(payload)
        if self.mqtt:
            self.mqtt.publish_status(payload)

    def publish_result(self, payload: dict) -> None:
        self.append_result(payload)
        show_result(payload)
        if self.mqtt:
            self.mqtt.publish_result(payload)

    def write_status(self, payload: dict) -> None:
        self.status_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def append_result(self, payload: dict, keep: int = 100) -> None:
        with self.results_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
        lines = self.results_file.read_text(encoding="utf-8").splitlines()
        if len(lines) > keep:
            self.results_file.write_text("\n".join(lines[-keep:]) + "\n", encoding="utf-8")

    def current_status(self) -> dict:
        payload = self.state.to_status_payload()
        payload.update(
            {
                "transport": self.transport,
                "data_dir": str(self.data_dir),
                "status_file": str(self.status_file),
                "results_file": str(self.results_file),
                "sample_audio": str(self.sample_audio),
            }
        )
        return payload

    def handle_command(self, command: str) -> dict:
        cmd = command.strip().lower()
        if cmd == "status":
            return {"type": "command_result", "command": cmd, "status": self.current_status()}
        if cmd == "play_test":
            if not self.sample_audio.exists():
                raise FileNotFoundError(f"sample audio not found: {self.sample_audio}")
            self.publish_status("testing", f"playing {self.sample_audio.name}")
            play_audio(self.config, self.sample_audio)
            self.publish_status("idle", "play_test done")
            return {"type": "command_result", "command": cmd, "status": "ok", "file": str(self.sample_audio)}
        if cmd == "record_test":
            test_config = copy.deepcopy(self.config)
            test_config["audio"]["record_seconds"] = min(int(test_config["audio"].get("record_seconds", 5)), 5)
            self.publish_status("testing", f"recording {self.last_record_file.name}")
            record_wav(test_config, self.last_record_file)
            self.publish_status("idle", "record_test done")
            return {"type": "command_result", "command": cmd, "status": "ok", "file": str(self.last_record_file)}
        if cmd == "tts_test":
            work_dir = runtime_dir(self.config)
            self.publish_status("testing", "requesting tts_test audio")
            ai_text, audio_bytes = self.ws.ask_agent("你好，请简单回复一句话")
            if not audio_bytes:
                raise RuntimeError("tts_test returned no audio")
            suffix = ".wav" if audio_bytes.startswith(b"RIFF") else ".pcm"
            audio_path = work_dir / f"tts_test_agent_audio{suffix}"
            audio_path.write_bytes(audio_bytes)
            self.publish_status("testing", f"playing {audio_path.name}")
            play_audio(self.config, audio_path)
            self.publish_status("idle", "tts_test done")
            return {
                "type": "command_result",
                "command": cmd,
                "status": "ok",
                "file": str(audio_path),
                "ai_text": ai_text,
                "bytes": len(audio_bytes),
            }
        if cmd == "restart":
            self.publish_status("restarting", "restart requested")
            threading.Timer(0.3, lambda: os._exit(0)).start()
            return {"type": "command_result", "command": cmd, "status": "restarting"}
        raise ValueError(f"unknown command: {command}")

    def dispatch_task(self, task: dict) -> None:
        if task.get("type") == "command" or task.get("command"):
            try:
                self.handle_command(str(task.get("command") or task.get("text") or "status"))
            except Exception as exc:
                payload = {"type": "command_result", "status": "error", "error": str(exc)}
                show_error(payload)
            return
        self.process_task_safely(task)

    def process_task(self, task: dict) -> dict:
        task_id = str(task.get("task_id") or int(time.time()))
        self.state.set_task(task_id)
        show_task(task)
        work_dir = runtime_dir(self.config)
        wav_path = work_dir / f"{task_id}.wav"
        agent_audio_path = work_dir / f"{task_id}_agent_audio.wav"

        task_config = copy.deepcopy(self.config)
        if task.get("record_seconds") is not None:
            task_config["audio"]["record_seconds"] = int(task["record_seconds"])

        record_seconds = int(task_config["audio"].get("record_seconds", 5))
        if self.file_mode or not task_config["audio"].get("streaming", True):
            self.publish_status("recording", f"task {task_id}")
            record_wav(task_config, wav_path)
            self.publish_status("asr", f"transcribing {task_id}")
            asr_text = self.ws.transcribe_wav(wav_path)
        else:
            self.publish_status("listening", f"streaming {task_id}")
            asr_text = self.ws.stream_asr_from_arecord(record_seconds)
        if not asr_text:
            raise RuntimeError("ASR returned empty text")

        self.state.set_result(asr_text=asr_text, ai_text="")
        self.publish_status("thinking", asr_text)
        try:
            if self.file_mode or not task_config["audio"].get("streaming", True):
                ai_text, audio_bytes = self.ws.ask_agent(asr_text)
            else:
                self.publish_status("speaking", "streaming agent audio")
                ai_text = self.ws.ask_agent_streaming(asr_text)
                audio_bytes = None
        except AgentResponseError as exc:
            self.state.set_result(asr_text=asr_text, ai_text=exc.partial_text)
            raise RuntimeError(f"{exc}; partial AI text saved") from exc
        self.state.set_result(asr_text=asr_text, ai_text=ai_text)

        if audio_bytes:
            if not audio_bytes.startswith(b"RIFF"):
                agent_audio_path = work_dir / f"{task_id}_agent_audio.pcm"
            agent_audio_path.write_bytes(audio_bytes)
            self.publish_status("speaking", f"playing {agent_audio_path.name}")
            play_audio(task_config, agent_audio_path)

        self.publish_status("idle", f"task {task_id} done")
        result = self.state.to_result_payload(task_id, status="ok")
        self.publish_result(result)
        return result

    def process_task_safely(self, task: dict) -> None:
        task_id = str(task.get("task_id") or "")
        try:
            self.process_task(task)
        except Exception as exc:
            message = str(exc)
            self.state.set_error(message, task_id=task_id)
            self.write_status(self.state.to_status_payload())
            payload = self.state.to_result_payload(task_id or str(int(time.time())), status="error")
            self.append_result(payload)
            show_error(payload)
            if self.mqtt:
                self.mqtt.publish_status(self.state.to_status_payload())
                self.mqtt.publish_result(payload)
            self.publish_status("idle", "waiting for next task")

    def run_mqtt(self) -> None:
        if not self.mqtt:
            raise RuntimeError("MQTT is disabled")
        self.publish_status("connecting", "connecting mqtt")
        self.mqtt.connect()
        self.mqtt.loop_start()
        self.publish_status("idle", "waiting for mqtt task")
        try:
            while True:
                task = self.tasks.get()
                self.dispatch_task(task)
        finally:
            self.mqtt.stop()

    def run_idle(self) -> None:
        self.publish_status("idle", "BLE UART active; waiting for tasks via BLE/web/mqtt")
        while True:
            time.sleep(60)

    def run_queued_tasks(self) -> None:
        while True:
            task = self.tasks.get()
            self.dispatch_task(task)

    def start_background_task_worker(self) -> threading.Thread:
        thread = threading.Thread(target=self.run_queued_tasks, name="task-worker", daemon=True)
        thread.start()
        return thread

    def run_ble_task_poller(self) -> None:
        offset = self.ble_task_file.stat().st_size if self.ble_task_file.exists() else 0
        while True:
            try:
                if self.ble_task_file.exists():
                    with self.ble_task_file.open("r", encoding="utf-8") as fp:
                        fp.seek(offset)
                        for line in fp:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                task = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if isinstance(task, dict):
                                self.enqueue_task(task)
                        offset = fp.tell()
            except Exception as exc:
                show_error({"type": "ble_task_poll", "error": str(exc)})
            time.sleep(0.5)

    def start_ble_task_poller(self) -> threading.Thread:
        thread = threading.Thread(target=self.run_ble_task_poller, name="ble-task-poller", daemon=True)
        thread.start()
        return thread

    def start_web(self):
        if not self.config.get("web", {}).get("enabled", True):
            return None
        return start_web_server(self)


def fake_task() -> dict:
    return {
        "task_id": "local-test",
        "type": "voice_answer",
        "prompt": "本地假任务：请录音并完成 ASR/AI/TTS 流程",
        "record_seconds": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="RK3506JS student Linux client.")
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--once", action="store_true", help="Run one local fake task without Bluetooth.")
    parser.add_argument("--mqtt", action="store_true", help="Use MQTT transport instead of Bluetooth.")
    parser.add_argument("--file-mode", action="store_true", help="Use record-then-upload and save-then-play fallback mode.")
    parser.add_argument("--check-env", action="store_true", help="Print board environment checks.")
    parser.add_argument("--check-ws", choices=["funasr", "agent", "both"], help="Check WebSocket connectivity.")
    args = parser.parse_args()

    if args.check_env:
        return run_env_check()

    config = load_config(Path(args.config))
    config["_config_path"] = str(Path(args.config).resolve())
    if args.check_ws:
        client = WsClient(config)
        if args.check_ws in ("funasr", "both"):
            client.check_funasr()
            print("FunASR WebSocket OK")
        if args.check_ws in ("agent", "both"):
            client.check_agent()
            print("chatAgent WebSocket OK")
        return 0

    app = StudentApp(config, transport="none" if args.once else ("mqtt" if args.mqtt else "none"))
    app.file_mode = args.file_mode
    if args.once:
        app.process_task_safely(fake_task())
        return 0

    app.start_web()
    app.start_ble_task_poller()
    if args.mqtt:
        app.run_mqtt()
    else:
        app.start_background_task_worker()
        app.run_idle()
    return 0


if __name__ == "__main__":
    sys.exit(main())
