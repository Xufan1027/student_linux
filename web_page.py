PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>学生端控制台</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --panel: #ffffff;
      --line: #e8edf5;
      --text: #1f2533;
      --muted: #7b8496;
      --blue: #2f6fdd;
      --green: #1f9d68;
      --cyan: #0f9ba8;
      --orange: #c8741c;
      --red: #b7335f;
      --purple: #7b35d8;
      color-scheme: light;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; min-height: 100%; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      letter-spacing: 0;
    }
    button, input, textarea, select { font: inherit; }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: #30384a;
      border-radius: 6px;
      min-height: 34px;
      padding: 0 12px;
      cursor: pointer;
    }
    button:hover { border-color: #c9d4e6; background: #f9fbff; }
    button.primary { background: var(--blue); color: #fff; border-color: var(--blue); }
    button.danger { background: #fff4f6; color: var(--red); border-color: #f4c5d0; }
    input, textarea, select {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      padding: 8px 10px;
      min-width: 0;
    }
    textarea {
      width: 100%;
      min-height: 118px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      line-height: 1.55;
    }
    pre {
      margin: 0;
      max-height: 360px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      border-radius: 6px;
      border: 1px solid #edf1f7;
      background: #fbfcff;
      color: #384154;
      padding: 12px;
      font-size: 12px;
      line-height: 1.55;
    }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; border-bottom: 1px solid #edf1f7; padding: 10px 4px; vertical-align: top; }
    th { width: 92px; color: var(--muted); font-weight: 600; }
    audio { width: 100%; margin-top: 12px; }
    .app { display: grid; grid-template-columns: 232px minmax(0, 1fr); min-height: 100vh; }
    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      background: #fff;
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
    }
    .brand {
      height: 58px;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 0 16px;
      border-bottom: 1px solid var(--line);
      font-weight: 700;
    }
    .logo {
      width: 30px;
      height: 30px;
      border-radius: 7px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #1e6be3, #19a7a6);
      color: #fff;
      font-weight: 800;
    }
    .nav { padding: 12px; flex: 1; overflow: auto; }
    .nav button {
      width: 100%;
      height: 42px;
      display: flex;
      align-items: center;
      gap: 10px;
      border: 0;
      background: transparent;
      color: #4e596d;
      justify-content: flex-start;
      margin-bottom: 4px;
    }
    .nav button.active { background: #edf4ff; color: var(--blue); font-weight: 700; }
    .nav .mark {
      width: 22px;
      height: 22px;
      display: grid;
      place-items: center;
      color: currentColor;
      font-size: 15px;
    }
    .side-user {
      border-top: 1px solid var(--line);
      padding: 14px;
      display: flex;
      gap: 10px;
      align-items: center;
      color: #4a5365;
    }
    .avatar {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: var(--purple);
      color: #fff;
      font-weight: 700;
    }
    .content { min-width: 0; }
    .topbar {
      height: 58px;
      background: rgba(255,255,255,.92);
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      position: sticky;
      top: 0;
      z-index: 4;
      backdrop-filter: blur(8px);
    }
    .crumb { display: flex; align-items: center; gap: 16px; font-weight: 700; }
    .fold { color: #9aa4b5; font-size: 24px; line-height: 1; }
    .top-actions { display: flex; align-items: center; gap: 10px; color: var(--muted); font-size: 13px; }
    main { padding: 22px 28px 34px; }
    .hero {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      gap: 20px;
      align-items: center;
      box-shadow: 0 8px 24px rgba(32,45,70,.04);
      margin-bottom: 18px;
    }
    .welcome { display: flex; align-items: center; gap: 14px; min-width: 0; }
    .welcome h1 { font-size: 18px; margin: 0 0 5px; }
    .welcome p { margin: 0; color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .range { display: flex; gap: 4px; background: #f6f8fb; padding: 4px; border-radius: 7px; white-space: nowrap; }
    .range button { border: 0; background: transparent; height: 32px; color: #788296; }
    .range button.active { background: #fff; color: var(--blue); box-shadow: 0 2px 8px rgba(35,56,91,.08); }
    .metrics { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px; margin-bottom: 22px; }
    .metric {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 134px;
      padding: 18px;
      position: relative;
      box-shadow: 0 8px 24px rgba(32,45,70,.035);
      overflow: hidden;
    }
    .metric .label { color: var(--muted); font-size: 13px; margin-bottom: 24px; }
    .metric .value { font-size: 26px; font-weight: 800; line-height: 1; overflow-wrap: anywhere; }
    .metric .sub { margin-top: 9px; color: #a2aabb; font-size: 12px; overflow-wrap: anywhere; }
    .metric .badge {
      position: absolute;
      top: 18px;
      right: 16px;
      width: 28px;
      height: 28px;
      border-radius: 7px;
      display: grid;
      place-items: center;
      font-weight: 800;
      font-size: 15px;
    }
    .blue { color: var(--blue); }
    .green { color: var(--green); }
    .cyan { color: var(--cyan); }
    .orange { color: var(--orange); }
    .red { color: var(--red); }
    .metric .badge.blue { background: #eef5ff; }
    .metric .badge.green { background: #edf9f3; }
    .metric .badge.cyan { background: #ecfbfc; }
    .metric .badge.orange { background: #fff6eb; }
    .metric .badge.red { background: #fff0f5; }
    .section-title { font-size: 15px; font-weight: 800; margin: 4px 0 14px; }
    .dash-grid { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(300px, .7fr); gap: 16px; margin-bottom: 20px; }
    .panel {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(32,45,70,.035);
      overflow: hidden;
      min-width: 0;
    }
    .panel-head {
      min-height: 54px;
      padding: 0 20px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .panel-title { font-weight: 800; font-size: 14px; }
    .panel-body { padding: 18px 20px; }
    .chart-wrap { height: 268px; position: relative; }
    canvas { width: 100%; height: 100%; display: block; }
    .donuts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .donut-card { min-height: 214px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; }
    .donut {
      width: 126px;
      height: 126px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: conic-gradient(var(--blue) var(--p, 0%), #eef1f6 0);
      position: relative;
    }
    .donut:after {
      content: "";
      width: 86px;
      height: 86px;
      border-radius: 50%;
      background: #fff;
      position: absolute;
    }
    .donut strong { position: relative; z-index: 1; font-size: 24px; }
    .donut span { position: relative; z-index: 1; display: block; color: var(--muted); font-size: 12px; text-align: center; margin-top: 4px; }
    .lower-grid { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(280px, .9fr); gap: 16px; margin-bottom: 20px; }
    .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .toolbar input { height: 34px; min-width: 180px; flex: 1; }
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      background: #edf9f3;
      color: var(--green);
      font-weight: 700;
      font-size: 12px;
    }
    .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
    .list { display: grid; gap: 10px; }
    .item {
      display: grid;
      grid-template-columns: 40px minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      border-bottom: 1px solid #f0f3f8;
      padding-bottom: 10px;
    }
    .item:last-child { border-bottom: 0; padding-bottom: 0; }
    .item-icon {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: #f3f7ff;
      color: var(--blue);
      font-weight: 800;
    }
    .item strong { display: block; font-size: 13px; margin-bottom: 3px; overflow-wrap: anywhere; }
    .item span { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .wide-grid { display: grid; grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr); gap: 16px; margin-bottom: 20px; }
    .json-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; }
    .muted { color: var(--muted); font-size: 12px; }
    .mobile-menu { display: none; }
    @media (max-width: 1180px) {
      .metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .dash-grid, .lower-grid, .wide-grid, .json-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 760px) {
      .app { grid-template-columns: 1fr; }
      .sidebar { position: static; height: auto; }
      .nav { display: none; }
      .side-user { display: none; }
      .topbar { position: static; padding: 0 14px; }
      main { padding: 14px; }
      .hero { align-items: flex-start; flex-direction: column; padding: 16px; }
      .range { width: 100%; overflow-x: auto; }
      .metrics { grid-template-columns: 1fr; }
      .donuts { grid-template-columns: 1fr; }
      .mobile-menu { display: inline-flex; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand"><div class="logo">S</div><span>学生端控制台</span></div>
      <nav class="nav">
        <button class="active"><span class="mark">⌂</span>首页</button>
      </nav>
      <div class="side-user">
        <div class="avatar">rk</div>
        <div><strong>RK3506JS</strong><div class="muted">root / student</div></div>
      </div>
    </aside>

    <div class="content">
      <div class="topbar">
        <div class="crumb"><span class="fold">»</span><span>首页</span></div>
        <div class="top-actions"><span id="clock"></span><div class="avatar">k</div><span>管理员</span></div>
      </div>

      <main>
        <section class="hero">
          <div class="welcome">
            <div class="avatar">k</div>
            <div>
              <h1>欢迎回来，RK3506JS</h1>
              <p><span id="hero-date"></span> · <span id="hero-ip">正在读取网络状态</span></p>
            </div>
          </div>
          <div class="range">
            <span class="status-pill" id="ble-pill"><span class="dot" id="ble-dot"></span><span id="ble-pill-text">BLE 检测中</span></span>
          </div>
        </section>

        <section class="metrics">
          <div class="metric"><div class="label">设备状态</div><div class="badge green">⌁</div><div class="value green" id="m-state">--</div><div class="sub" id="m-message"></div></div>
          <div class="metric"><div class="label">可用内存</div><div class="badge blue">M</div><div class="value blue" id="m-memory">--</div><div class="sub" id="m-memory-sub"></div></div>
          <div class="metric"><div class="label">磁盘空间</div><div class="badge orange">D</div><div class="value orange" id="m-disk">--</div><div class="sub" id="m-disk-sub"></div></div>
          <div class="metric"><div class="label">蓝牙状态</div><div class="badge cyan">B</div><div class="value cyan" id="m-ble">--</div><div class="sub" id="m-ble-sub"></div></div>
          <div class="metric"><div class="label">最近结果</div><div class="badge red">R</div><div class="value red" id="m-results">0</div><div class="sub">results.jsonl</div></div>
          <div class="metric"><div class="label">录音文件</div><div class="badge blue">A</div><div class="value blue" id="m-record">--</div><div class="sub" id="m-record-sub"></div></div>
        </section>

        <div class="section-title">运行概览</div>
        <div class="dash-grid">
          <section class="panel">
            <div class="panel-head"><div class="panel-title">资源趋势</div><div class="muted">内存 / 磁盘</div></div>
            <div class="panel-body"><div class="chart-wrap"><canvas id="trend" width="940" height="300"></canvas></div></div>
          </section>
          <div class="donuts">
            <section class="panel donut-card">
              <div class="panel-title">内存使用率</div>
              <div class="donut" id="memDonut"><div><strong id="memPercent">0%</strong><span>已使用</span></div></div>
              <div class="muted" id="memDonutText">等待数据</div>
            </section>
            <section class="panel donut-card">
              <div class="panel-title">磁盘使用率</div>
              <div class="donut" id="diskDonut" style="--p:0%; background: conic-gradient(var(--green) var(--p), #eef1f6 0);"><div><strong id="diskPercent">0%</strong><span>已使用</span></div></div>
              <div class="muted" id="diskDonutText">等待数据</div>
            </section>
          </div>
        </div>

        <div class="section-title">设备操作</div>
        <div class="lower-grid">
          <section class="panel">
            <div class="panel-head"><div class="panel-title">快捷操作</div><span class="status-pill"><span class="dot"></span><span id="onlineText">运行中</span></span></div>
            <div class="panel-body">
              <div class="toolbar">
                <button onclick="refreshAll()">刷新</button>
                <button onclick="runCommand('status')">status</button>
                <button onclick="runCommand('play_test')">play_test</button>
                <button onclick="runCommand('tts_test')">tts_test</button>
                <button onclick="runCommand('record_test')">record_test</button>
                <button onclick="selfCheck()">一键自检</button>
                <button class="danger" onclick="confirmRestart()">restart</button>
              </div>
              <div class="toolbar" style="margin-top:12px">
                <input id="customCommand" value="status">
                <button class="primary" onclick="runCustomCommand()">发送命令</button>
              </div>
              <pre id="result" style="margin-top:14px"></pre>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head"><div class="panel-title">系统信息</div><button onclick="loadHealth()">刷新</button></div>
            <div class="panel-body"><table><tbody id="healthTable"></tbody></table></div>
          </section>
        </div>

        <section class="panel" style="margin-bottom:20px">
          <div class="panel-head"><div class="panel-title">录音文件</div><div class="toolbar"><button onclick="loadRecord()">刷新</button><button onclick="runCommand('record_test')">重新录音</button><a href="/files/last_record.wav" download><button>下载</button></a></div></div>
          <div class="panel-body">
            <div class="muted" id="recordInfo"></div>
            <audio id="recordAudio" controls src="/files/last_record.wav"></audio>
          </div>
        </section>

        <div class="wide-grid">
          <section class="panel">
            <div class="panel-head"><div class="panel-title">最近结果</div><button onclick="loadResults()">刷新结果</button></div>
            <div class="panel-body">
              <div class="list" id="resultsList"></div>
              <pre id="results" style="margin-top:14px"></pre>
            </div>
          </section>
          <section class="panel">
            <div class="panel-head"><div class="panel-title">发送任务 JSON</div><button class="primary" onclick="sendTask()">执行任务</button></div>
            <div class="panel-body">
              <textarea id="task">{"task_id":"web-demo","type":"voice_answer","prompt":"请回答问题","record_seconds":5}</textarea>
            </div>
          </section>
        </div>

        <div class="json-grid">
          <section class="panel">
            <div class="panel-head"><div class="panel-title">状态 JSON</div></div>
            <div class="panel-body"><pre id="status">loading...</pre></div>
          </section>
          <section class="panel">
            <div class="panel-head"><div class="panel-title">配置查看</div><button onclick="loadConfig()">刷新配置</button></div>
            <div class="panel-body"><pre id="config"></pre></div>
          </section>
        </div>

        <section class="panel" style="margin-bottom:20px">
          <div class="panel-head"><div class="panel-title">WebSocket 配置</div><button class="primary" onclick="saveWsConfig()">保存并生效</button></div>
          <div class="panel-body">
            <table>
              <tbody>
                <tr><th>ASR 地址</th><td><input id="cfg-funasr" style="width:100%" placeholder="ws://..."></td></tr>
                <tr><th>Agent 地址</th><td><input id="cfg-agent" style="width:100%" placeholder="ws://..."></td></tr>
                <tr><th>Agent 用户</th><td><input id="cfg-agent-user" style="width:100%"></td></tr>
              </tbody>
            </table>
            <pre id="cfg-result" style="margin-top:12px"></pre>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div class="panel-title">日志</div>
            <div class="toolbar">
              <button onclick="loadLog()">刷新日志</button>
              <label class="muted"><input type="checkbox" id="autoLog" checked> 自动刷新</label>
              <label class="muted"><input type="checkbox" id="onlyError"> 只看 error</label>
              <button onclick="clearLogView()">清屏显示</button>
              <a href="/api/log" download="student.log"><button>下载日志</button></a>
            </div>
          </div>
          <div class="panel-body"><pre id="log"></pre></div>
        </section>
      </main>
    </div>
  </div>

<script>
async function refresh() {
  const r = await fetch('/api/status');
  const data = await r.json();
  document.getElementById('status').textContent = JSON.stringify(data, null, 2);
  document.getElementById('m-state').textContent = data.state || '--';
  document.getElementById('m-message').textContent = data.message || '';
  document.getElementById('onlineText').textContent = data.state || '运行中';
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
  const bleOn = !!data.bluetooth?.ble_uuid;
  const bleConnected = data.bluetooth?.connected && data.bluetooth.connected.trim().length > 0;
  document.getElementById('m-ble').textContent = bleConnected ? '已连接' : (bleOn ? 'BLE 广播中' : '未知');
  document.getElementById('m-ble-sub').textContent = data.bluetooth?.connected || data.bluetooth?.alias || '';
  const pill = document.getElementById('ble-pill');
  const dot = document.getElementById('ble-dot');
  const pillText = document.getElementById('ble-pill-text');
  if (bleConnected) {
    pill.style.background = '#edf9f3'; pill.style.color = 'var(--green)';
    dot.style.background = 'var(--green)';
    pillText.textContent = 'BLE 已连接：' + data.bluetooth.connected.split('\\n')[0].trim();
  } else if (bleOn) {
    pill.style.background = '#eef5ff'; pill.style.color = 'var(--blue)';
    dot.style.background = 'var(--blue)';
    pillText.textContent = 'BLE 广播中，等待连接';
  } else {
    pill.style.background = '#fff6eb'; pill.style.color = 'var(--orange)';
    dot.style.background = 'var(--orange)';
    pillText.textContent = 'BLE 状态未知';
  }
  document.getElementById('hero-ip').textContent = data.ip ? `wlan0 ${data.ip}` : '未读取到 wlan0 地址';

  const memPct = percentFromValues(data.memory?.used, data.memory?.total);
  const diskPct = percentText(data.disk?.use_percent);
  setDonut('memDonut', 'memPercent', 'memDonutText', memPct, `${data.memory?.used || '--'} / ${data.memory?.total || '--'}`, '#2f6fdd');
  setDonut('diskDonut', 'diskPercent', 'diskDonutText', diskPct, `${data.disk?.used || '--'} / ${data.disk?.size || '--'}`, '#1f9d68');

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
  document.getElementById('m-results').textContent = String(rows.length);
  document.getElementById('resultsList').innerHTML = rows.slice(0, 6).map(row => {
    const time = row.timestamp ? new Date(row.timestamp * 1000).toLocaleString() : '暂无时间';
    const title = row.task_id || row.command || '任务记录';
    const desc = row.ai_text || row.asr_text || row.raw || row.status || '';
    return `<div class="item"><div class="item-icon">R</div><div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(time)} · ${escapeHtml(desc)}</span></div><strong class="${row.status === 'error' ? 'red' : 'green'}">${escapeHtml(row.status || '')}</strong></div>`;
  }).join('') || '<div class="muted">暂无结果</div>';
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
function confirmRestart() { runCommand('restart'); }
async function selfCheck() {
  await loadHealth();
  document.getElementById('result').textContent = '自检完成：请查看总览、系统信息、录音文件和日志。';
}
async function loadConfig() {
  const r = await fetch('/api/config');
  const data = await r.json();
  document.getElementById('config').textContent = JSON.stringify(data, null, 2);
  if (data.websocket) {
    document.getElementById('cfg-funasr').value = data.websocket.funasr_url || '';
    document.getElementById('cfg-agent').value = data.websocket.agent_url || '';
    document.getElementById('cfg-agent-user').value = data.websocket.agent_user || '';
  }
}
async function saveWsConfig() {
  const payload = {
    funasr_url: document.getElementById('cfg-funasr').value.trim(),
    agent_url: document.getElementById('cfg-agent').value.trim(),
    agent_user: document.getElementById('cfg-agent-user').value.trim(),
  };
  const r = await fetch('/api/config/save', {method:'POST', body: JSON.stringify(payload)});
  const result = await r.json();
  document.getElementById('cfg-result').textContent = JSON.stringify(result, null, 2);
}
async function loadRecord() {
  const r = await fetch('/api/record');
  const data = await r.json();
  document.getElementById('recordInfo').textContent = data.exists ? `${data.path} | ${data.size_human} | ${data.mtime}` : '暂无录音文件';
  document.getElementById('m-record').textContent = data.exists ? data.size_human : '--';
  document.getElementById('m-record-sub').textContent = data.exists ? data.mtime : '暂无录音';
  document.getElementById('recordAudio').src = '/files/last_record.wav?t=' + Date.now();
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function clearLogView() { document.getElementById('log').textContent = ''; }
function parseSize(text) {
  const m = String(text || '').match(/^([0-9.]+)([KMGT]?i?|[KMGT]?B?)$/);
  if (!m) return 0;
  const unit = m[2].replace('B', '');
  const units = {K:1/1024, Ki:1/1024, M:1, Mi:1, G:1024, Gi:1024, T:1048576, Ti:1048576};
  return Number(m[1]) * (units[unit] || 1);
}
function percentText(text) {
  const n = Number(String(text || '').replace('%', ''));
  return Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
}
function percentFromValues(used, total) {
  const u = parseSize(used);
  const t = parseSize(total);
  return t > 0 ? Math.round((u / t) * 100) : 0;
}
function setDonut(id, textId, subId, pct, sub, color) {
  const safe = Math.max(0, Math.min(100, Number(pct) || 0));
  const el = document.getElementById(id);
  el.style.background = `conic-gradient(${color} ${safe}%, #eef1f6 0)`;
  document.getElementById(textId).textContent = `${safe}%`;
  document.getElementById(subId).textContent = sub;
}
function drawTrend() {
  const canvas = document.getElementById('trend');
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = '#eef2f7'; ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++) {
    const y = 30 + i * ((h - 70) / 4);
    ctx.beginPath(); ctx.moveTo(50, y); ctx.lineTo(w - 24, y); ctx.stroke();
  }
  drawAreaLine(ctx, trends.map(p => p.mem), '#2f6fdd', 'rgba(47,111,221,.12)', w, h);
  drawAreaLine(ctx, trends.map(p => p.disk), '#1f9d68', 'rgba(31,157,104,.10)', w, h);
  ctx.fillStyle = '#7b8496'; ctx.font = '13px system-ui';
  ctx.fillText('可用内存', w / 2 - 64, 24);
  ctx.fillStyle = '#2f6fdd'; ctx.fillText('●', w / 2 - 82, 24);
  ctx.fillStyle = '#7b8496'; ctx.fillText('磁盘可用', w / 2 + 34, 24);
  ctx.fillStyle = '#1f9d68'; ctx.fillText('●', w / 2 + 16, 24);
}
function drawAreaLine(ctx, values, color, fill, w, h) {
  if (values.length < 2) return;
  const max = Math.max(...values, 1);
  const left = 50, right = w - 24, top = 34, bottom = h - 34;
  const points = values.map((v, i) => [left + i * ((right - left) / Math.max(values.length - 1, 1)), bottom - (v / max) * (bottom - top)]);
  ctx.beginPath();
  points.forEach(([x, y], i) => i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y));
  ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.stroke();
  ctx.lineTo(points[points.length - 1][0], bottom);
  ctx.lineTo(points[0][0], bottom);
  ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
  const last = points[points.length - 1];
  ctx.beginPath(); ctx.arc(last[0], last[1], 4, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill();
}
function tick() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleString();
  document.getElementById('hero-date').textContent = now.toLocaleDateString('zh-CN', {year:'numeric', month:'long', day:'numeric', weekday:'long'});
}
async function refreshAll() {
  const jobs = [refresh(), loadHealth(), loadResults(), loadConfig(), loadRecord()];
  if (document.getElementById('autoLog').checked) jobs.push(loadLog());
  await Promise.allSettled(jobs);
}
tick(); refreshAll();
setInterval(tick, 1000);
setInterval(refreshAll, 5000);
</script>
</body>
</html>
"""
