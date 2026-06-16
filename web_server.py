import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Student RK3506JS</title>
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; margin: 0; background: #f4f6f8; color: #171a1f; }
    header { background: #102033; color: white; padding: 14px 18px; display: flex; justify-content: space-between; gap: 12px; align-items: center; }
    header span { color: #b7c7d9; font-size: 13px; }
    main { max-width: 1160px; margin: 0 auto; padding: 16px; }
    h3 { margin: 0 0 10px; font-size: 16px; }
    section { background: white; border: 1px solid #d7dde5; border-radius: 6px; padding: 14px; margin-bottom: 14px; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
    .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .metric { border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #fbfcfe; min-height: 78px; }
    .label { color: #607086; font-size: 12px; }
    .value { font-size: 22px; font-weight: 700; margin-top: 5px; overflow-wrap: anywhere; }
    .sub { color: #607086; font-size: 12px; margin-top: 3px; overflow-wrap: anywhere; }
    .toolbar { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    button { padding: 8px 12px; border: 1px solid #9aa7b7; border-radius: 5px; background: #fff; cursor: pointer; }
    button.primary { background: #0f62fe; color: white; border-color: #0f62fe; }
    button.danger { background: #ba1a1a; color: white; border-color: #ba1a1a; }
    input, textarea { border: 1px solid #b8c2cf; border-radius: 5px; padding: 8px; font: inherit; }
    input { min-width: 220px; }
    pre { white-space: pre-wrap; word-break: break-word; background: #101418; color: #e8eef7; padding: 12px; border-radius: 5px; max-height: 420px; overflow: auto; }
    textarea { width: 100%; min-height: 120px; font-family: ui-monospace, monospace; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; border-bottom: 1px solid #e3e7ed; padding: 8px; vertical-align: top; }
    th { color: #607086; font-weight: 600; }
    .ok { color: #137333; }
    .warn { color: #9a6700; }
    .muted { color: #607086; font-size: 12px; }
    audio { width: 100%; margin-top: 10px; }
    canvas { width: 100%; height: 120px; border: 1px solid #d7dde5; border-radius: 5px; }
    @media (max-width: 860px) { .grid, .two { grid-template-columns: 1fr; } header { align-items: flex-start; flex-direction: column; } }
  </style>
</head>
<body>
  <header>
    <strong>Student RK3506JS</strong>
    <span id="clock"></span>
  </header>
  <main>
    <section>
      <h3>总览</h3>
      <div class="grid">
        <div class="metric"><div class="label">设备状态</div><div class="value" id="m-state">--</div><div class="sub" id="m-message"></div></div>
        <div class="metric"><div class="label">可用内存</div><div class="value" id="m-memory">--</div><div class="sub" id="m-memory-sub"></div></div>
        <div class="metric"><div class="label">磁盘空间</div><div class="value" id="m-disk">--</div><div class="sub" id="m-disk-sub"></div></div>
        <div class="metric"><div class="label">蓝牙/BLE</div><div class="value" id="m-ble">--</div><div class="sub" id="m-ble-sub"></div></div>
      </div>
    </section>

    <div class="two">
      <section>
        <h3>快捷操作</h3>
        <div class="toolbar">
          <button onclick="refreshAll()">刷新</button>
          <button onclick="runCommand('status')">status</button>
          <button onclick="runCommand('play_test')">play_test</button>
          <button onclick="runCommand('record_test')">record_test</button>
          <button class="danger" onclick="confirmRestart()">restart</button>
          <button onclick="selfCheck()">一键自检</button>
        </div>
        <div class="toolbar" style="margin-top:10px">
          <input id="customCommand" value="status">
          <button class="primary" onclick="runCustomCommand()">发送命令</button>
        </div>
        <pre id="result"></pre>
      </section>

      <section>
        <h3>系统信息</h3>
        <table>
          <tbody id="healthTable"></tbody>
        </table>
      </section>
    </div>

    <div class="two">
      <section>
        <h3>BLE 调试</h3>
        <div class="toolbar">
          <button onclick="loadBle()">刷新 BLE</button>
          <button onclick="runCommand('status')">发送 status</button>
        </div>
        <pre id="ble"></pre>
      </section>
      <section>
        <h3>录音文件</h3>
        <div class="toolbar">
          <button onclick="loadRecord()">刷新文件</button>
          <button onclick="runCommand('record_test')">重新录音</button>
          <button onclick="runCommand('play_test')">板子播放测试音频</button>
          <a href="/files/last_record.wav" download><button>下载 last_record.wav</button></a>
        </div>
        <div class="muted" id="recordInfo"></div>
        <audio id="recordAudio" controls src="/files/last_record.wav"></audio>
      </section>
    </div>

    <section>
      <h3>状态 JSON</h3>
      <pre id="status">loading...</pre>
    </section>

    <section>
      <h3>发送任务 JSON</h3>
      <textarea id="task">{"task_id":"web-demo","type":"voice_answer","prompt":"请回答问题","record_seconds":5}</textarea>
      <br>
      <button class="primary" onclick="sendTask()">执行任务</button>
    </section>

    <div class="two">
      <section>
        <h3>最近结果</h3>
        <button onclick="loadResults()">刷新结果</button>
        <table>
          <thead><tr><th>时间</th><th>任务</th><th>状态</th><th>ASR</th><th>AI</th></tr></thead>
          <tbody id="resultsTable"></tbody>
        </table>
        <pre id="results"></pre>
      </section>
      <section>
        <h3>音频与蓝牙</h3>
        <pre id="devices"></pre>
      </section>
    </div>

    <div class="two">
      <section>
        <h3>配置查看</h3>
        <button onclick="loadConfig()">刷新配置</button>
        <pre id="config"></pre>
      </section>
      <section>
        <h3>内存/磁盘趋势</h3>
        <canvas id="trend" width="520" height="140"></canvas>
        <div class="muted">浏览器端只保留最近 120 个点，不写入板子。</div>
      </section>
    </div>

    <section>
      <h3>日志</h3>
      <div class="toolbar">
        <button onclick="loadLog()">刷新日志</button>
        <label><input type="checkbox" id="autoLog" checked> 自动刷新</label>
        <label><input type="checkbox" id="onlyError"> 只看 error</label>
        <button onclick="clearLogView()">清屏显示</button>
        <a href="/api/log" download="student.log"><button>下载日志</button></a>
      </div>
      <pre id="log"></pre>
    </section>
  </main>
<script>
async function refresh() {
  const r = await fetch('/api/status');
  const data = await r.json();
  document.getElementById('status').textContent = JSON.stringify(data, null, 2);
  document.getElementById('m-state').textContent = data.state || '--';
  document.getElementById('m-message').textContent = data.message || '';
}
async function loadLog() {
  const r = await fetch('/api/log');
  let text = await r.text();
  if (document.getElementById('onlyError').checked) {
    text = text.split('\\n').filter(line => /error|failed|Traceback|Exception/i.test(line)).join('\\n');
  }
  const log = document.getElementById('log');
  log.textContent = text;
  log.scrollTop = log.scrollHeight;
}
const trends = [];
async function loadHealth() {
  const r = await fetch('/api/health');
  const data = await r.json();
  document.getElementById('m-memory').textContent = data.memory?.available || '--';
  document.getElementById('m-memory-sub').textContent = `used ${data.memory?.used || '--'} / total ${data.memory?.total || '--'}`;
  document.getElementById('m-disk').textContent = data.disk?.available || '--';
  document.getElementById('m-disk-sub').textContent = `${data.disk?.mount || '/userdata'} used ${data.disk?.used || '--'} / ${data.disk?.size || '--'}`;
  document.getElementById('m-ble').textContent = data.bluetooth?.ble_uuid ? 'BLE on' : 'unknown';
  document.getElementById('m-ble-sub').textContent = data.bluetooth?.connected || data.bluetooth?.alias || '';
  const rows = [
    ['主机', data.host || ''],
    ['系统', data.os || ''],
    ['Python', data.python || ''],
    ['IP', data.ip || ''],
    ['服务进程', data.processes || ''],
    ['BLE UUID', data.bluetooth?.ble_uuid || ''],
    ['声卡录音', data.audio?.capture || ''],
    ['声卡播放', data.audio?.playback || '']
  ];
  document.getElementById('healthTable').innerHTML = rows.map(([k, v]) => `<tr><th>${k}</th><td>${escapeHtml(String(v))}</td></tr>`).join('');
  document.getElementById('devices').textContent = JSON.stringify({bluetooth: data.bluetooth, audio: data.audio}, null, 2);
  trends.push({t: Date.now(), mem: parseSize(data.memory?.available), disk: parseSize(data.disk?.available)});
  while (trends.length > 120) trends.shift();
  drawTrend();
}
async function loadResults() {
  const r = await fetch('/api/results');
  const text = await r.text();
  document.getElementById('results').textContent = text;
  const rows = text.trim().split('\\n').filter(Boolean).slice(-20).reverse().map(line => {
    try { return JSON.parse(line); } catch { return {raw: line}; }
  });
  document.getElementById('resultsTable').innerHTML = rows.map(row => {
    const time = row.timestamp ? new Date(row.timestamp * 1000).toLocaleString() : '';
    return `<tr><td>${escapeHtml(time)}</td><td>${escapeHtml(row.task_id || '')}</td><td>${escapeHtml(row.status || '')}</td><td>${escapeHtml(row.asr_text || row.raw || '')}</td><td>${escapeHtml(row.ai_text || '')}</td></tr>`;
  }).join('');
}
async function runCommand(command) {
  if (command === 'restart' && !confirm('确定要重启学生端服务吗？')) return;
  const r = await fetch('/api/command', {method:'POST', body: JSON.stringify({command})});
  document.getElementById('result').textContent = JSON.stringify(await r.json(), null, 2);
  refreshAll();
}
async function runCustomCommand() {
  const command = document.getElementById('customCommand').value;
  await runCommand(command);
}
async function sendTask() {
  const task = JSON.parse(document.getElementById('task').value);
  const r = await fetch('/api/task', {method:'POST', body: JSON.stringify(task)});
  document.getElementById('result').textContent = JSON.stringify(await r.json(), null, 2);
  refreshAll();
}
function confirmRestart() {
  runCommand('restart');
}
async function selfCheck() {
  await loadHealth();
  document.getElementById('result').textContent = '自检完成：请查看总览、系统信息、BLE 调试、音频与蓝牙。';
}
async function loadBle() {
  const r = await fetch('/api/ble');
  document.getElementById('ble').textContent = JSON.stringify(await r.json(), null, 2);
}
async function loadConfig() {
  const r = await fetch('/api/config');
  document.getElementById('config').textContent = JSON.stringify(await r.json(), null, 2);
}
async function loadRecord() {
  const r = await fetch('/api/record');
  const data = await r.json();
  document.getElementById('recordInfo').textContent = data.exists ? `${data.path} | ${data.size_human} | ${data.mtime}` : '暂无录音文件';
  document.getElementById('recordAudio').src = '/files/last_record.wav?t=' + Date.now();
}
function escapeHtml(value) {
  return value.replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function clearLogView() {
  document.getElementById('log').textContent = '';
}
function parseSize(text) {
  const m = String(text || '').match(/^([0-9.]+)([KMGT]?i?|[KMGT]?)$/);
  if (!m) return 0;
  const units = {K:1/1024, Ki:1/1024, M:1, Mi:1, G:1024, Gi:1024, T:1048576, Ti:1048576};
  return Number(m[1]) * (units[m[2]] || 1);
}
function drawTrend() {
  const canvas = document.getElementById('trend');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#d7dde5'; ctx.beginPath(); ctx.moveTo(30, 10); ctx.lineTo(30, 120); ctx.lineTo(500, 120); ctx.stroke();
  drawLine(ctx, trends.map(p => p.mem), '#0f62fe');
  drawLine(ctx, trends.map(p => p.disk), '#137333');
  ctx.fillStyle = '#171a1f'; ctx.fillText('mem', 36, 20); ctx.fillText('disk', 76, 20);
}
function drawLine(ctx, values, color) {
  if (values.length < 2) return;
  const max = Math.max(...values, 1);
  ctx.strokeStyle = color; ctx.beginPath();
  values.forEach((v, i) => {
    const x = 30 + i * (470 / Math.max(values.length - 1, 1));
    const y = 120 - (v / max) * 100;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
}
function tick() {
  document.getElementById('clock').textContent = new Date().toLocaleString();
}
async function refreshAll() {
  const jobs = [refresh(), loadHealth(), loadResults(), loadBle(), loadConfig(), loadRecord()];
  if (document.getElementById('autoLog').checked) jobs.push(loadLog());
  await Promise.all(jobs);
}
tick(); refreshAll();
setInterval(tick, 1000);
setInterval(refreshAll, 5000);
</script>
</body>
</html>
"""


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def _tail(path: Path, lines: int) -> str:
    if not path.exists():
        return ""
    data = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(data[-lines:])


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f}{unit}" if unit != "B" else f"{int(value)}B"
        value /= 1024
    return f"{size}B"


def _run_text(cmd: list[str], timeout: float = 3.0) -> str:
    try:
        result = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return result.stdout.strip()
    except Exception as exc:
        return f"error: {exc}"


def _parse_free() -> dict:
    output = _run_text(["free", "-h"])
    lines = output.splitlines()
    if len(lines) < 2:
        return {"raw": output}
    parts = lines[1].split()
    if len(parts) < 7:
        return {"raw": output}
    return {"total": parts[1], "used": parts[2], "free": parts[3], "buff_cache": parts[5], "available": parts[6]}


def _parse_disk() -> dict:
    output = _run_text(["df", "-h", "/userdata"])
    lines = output.splitlines()
    if len(lines) < 2:
        return {"raw": output}
    parts = lines[1].split()
    if len(parts) < 6:
        return {"raw": output}
    return {"filesystem": parts[0], "size": parts[1], "used": parts[2], "available": parts[3], "use_percent": parts[4], "mount": parts[5]}


def _health() -> dict:
    bt = _run_text(["bluetoothctl", "show"], timeout=4)
    capture = _run_text(["arecord", "-l"], timeout=3)
    playback = _run_text(["aplay", "-l"], timeout=3)
    connected = _run_text(["bluetoothctl", "devices", "Connected"], timeout=3)
    return {
        "host": _run_text(["hostname"]),
        "os": _run_text(["uname", "-a"]),
        "python": _run_text(["python3", "--version"]),
        "ip": _run_text(["sh", "-c", "ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2}'"]),
        "memory": _parse_free(),
        "disk": _parse_disk(),
        "processes": _run_text(["sh", "-c", "ps w | grep -E 'main.py|ble_uart_dbus|rfcomm' | grep -v grep"], timeout=3),
        "bluetooth": {
            "alias": next((line.strip() for line in bt.splitlines() if "Alias:" in line), ""),
            "ble_uuid": "6e400001-b5a3-f393-e0a9-e50e24dcca9e" if "6e400001-b5a3-f393-e0a9-e50e24dcca9e" in bt.lower() else "",
            "connected": connected,
            "raw": bt,
        },
        "audio": {
            "capture": capture,
            "playback": playback,
        },
    }


def _redact_config(config: dict) -> dict:
    hidden = {"password", "token", "secret", "key"}

    def redact(value):
        if isinstance(value, dict):
            return {k: ("***" if any(word in k.lower() for word in hidden) and v else redact(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        return value

    return redact(config)


def _record_info(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    stat = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "size": stat.st_size,
        "size_human": _human_size(stat.st_size),
        "mtime": __import__("time").strftime("%Y-%m-%d %H:%M:%S", __import__("time").localtime(stat.st_mtime)),
    }


def start_web_server(app) -> ThreadingHTTPServer:
    web_cfg = app.config.get("web", {})
    storage = app.config.get("storage", {})
    host = web_cfg.get("host", "0.0.0.0")
    port = int(web_cfg.get("port", 8080))
    log_file = Path(storage.get("log_file", "/userdata/student/student.log"))
    results_file = Path(storage.get("results_file", "/userdata/student/results.jsonl"))
    last_record_file = Path(storage.get("last_record_file", "/userdata/student/last_record.wav"))
    ble_rx_file = Path("/userdata/student/ble_rx.txt")
    log_tail_lines = int(web_cfg.get("log_tail_lines", 120))

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str = "application/json") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
            elif path == "/api/status":
                self._send(200, json.dumps(app.current_status(), ensure_ascii=False, indent=2).encode("utf-8"))
            elif path == "/api/log":
                self._send(200, _tail(log_file, log_tail_lines).encode("utf-8"), "text/plain; charset=utf-8")
            elif path == "/api/results":
                self._send(200, _tail(results_file, 60).encode("utf-8"), "text/plain; charset=utf-8")
            elif path == "/api/health":
                self._send(200, json.dumps(_health(), ensure_ascii=False, indent=2).encode("utf-8"))
            elif path == "/api/ble":
                payload = {
                    "rx_tail": _tail(ble_rx_file, 30),
                    "connected": _run_text(["bluetoothctl", "devices", "Connected"], timeout=3),
                    "show": _run_text(["bluetoothctl", "show"], timeout=4),
                    "tx_tail": "\n".join(line for line in _tail(log_file, 80).splitlines() if "BLE TX" in line or "BLE RX" in line)[-5000:],
                }
                self._send(200, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
            elif path == "/api/config":
                self._send(200, json.dumps(_redact_config(app.config), ensure_ascii=False, indent=2).encode("utf-8"))
            elif path == "/api/record":
                self._send(200, json.dumps(_record_info(last_record_file), ensure_ascii=False, indent=2).encode("utf-8"))
            elif path == "/files/last_record.wav":
                if not last_record_file.exists():
                    self._send(404, b'{"error":"not_found"}')
                    return
                self._send(200, last_record_file.read_bytes(), "audio/wav")
            else:
                self._send(404, b'{"error":"not_found"}')

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {k: v[0] for k, v in parse_qs(body).items()}
            try:
                if self.path == "/api/command":
                    result = app.handle_command(str(payload.get("command", "status")))
                elif self.path == "/api/task":
                    result = app.process_task(payload)
                else:
                    self._send(404, b'{"error":"not_found"}')
                    return
                self._send(200, json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
            except Exception as exc:
                self._send(500, json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False).encode("utf-8"))

        def log_message(self, fmt, *args) -> None:
            print("web:", fmt % args, flush=True)

    server = ReusableThreadingHTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, name="web", daemon=True)
    thread.start()
    print(f"Web UI: http://{host}:{port}", flush=True)
    return server
