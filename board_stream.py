import json
import socket
import threading
import time
from pathlib import Path

RESULTS_FILE = Path("/userdata/student/results.jsonl")
HOST = "0.0.0.0"
PORT = 9001


def send_line(conn: socket.socket, obj) -> bool:
    try:
        line = (json.dumps(obj, ensure_ascii=False) if isinstance(obj, dict) else str(obj))
        conn.sendall((line + "\n").encode("utf-8"))
        return True
    except Exception:
        return False


def handle_client(conn: socket.socket, addr) -> None:
    print(f"[board_stream] client connected: {addr}", flush=True)
    send_line(conn, {"type": "connected", "message": "board stream ready"})

    # 后台线程：监听 results.jsonl，有新结果就推给客户端
    def watch_results():
        offset = RESULTS_FILE.stat().st_size if RESULTS_FILE.exists() else 0
        while True:
            try:
                if RESULTS_FILE.exists():
                    with RESULTS_FILE.open("r", encoding="utf-8") as fp:
                        fp.seek(offset)
                        for line in fp:
                            line = line.strip()
                            if line:
                                if not send_line(conn, line):
                                    return
                        offset = fp.tell()
            except Exception as e:
                send_line(conn, {"type": "error", "error": str(e)})
            time.sleep(0.5)

    t = threading.Thread(target=watch_results, daemon=True)
    t.start()

    # 主线程：接收客户端发来的命令
    try:
        from bluetooth_protocol import DEFAULT_BLE_TASK_FILE, append_ble_task
        buf = ""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buf += data.decode("utf-8", errors="replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    task = json.loads(line)
                except json.JSONDecodeError:
                    task = {"type": "command", "command": line}
                append_ble_task(task)
                send_line(conn, {"type": "ack", "received": task})
    except Exception:
        pass
    finally:
        conn.close()
        print(f"[board_stream] client disconnected: {addr}", flush=True)


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[board_stream] listening on {HOST}:{PORT}", flush=True)
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
