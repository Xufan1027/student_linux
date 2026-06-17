# 板子主动推送设计说明

## 核心问题

板子（RK3506JS，192.168.3.126）向连接它的设备主动发送消息，**必须知道对方的 IP**，或者让对方维持一条持久连接。

绑定机制解决了这个问题：**绑定时客户端主动连板子，板子在这一刻拿到对方 IP 或建立持久连接**，之后就能反向推送。

---

## 方案对比

### 方案 A：客户端来拉（当前架构）

```
Unity/C# ──RunCommand──▶ 板子 sshreceiver.py ──▶ 返回结果
```

- 板子不需要知道任何人的 IP
- Unity 用 SSH.NET 的 `RunCommand`，阻塞等待结果，最简单
- **缺点**：板子无法主动推，只能被动响应

适合：任务下发 + 一次性查询结果

---

### 方案 B：绑定时上报 IP，板子回调

```
Unity ──POST /api/bind {"callback_url":"http://192.168.1.50:9000/result"}──▶ 板子
板子记住 callback_url
板子有结果 ──POST──▶ http://192.168.1.50:9000/result
```

**板子端**（`web_server.py` 新增）：

```python
# POST /api/bind
# body: {"device_id": "unity-001", "callback_url": "http://192.168.1.50:9000/result"}
# 板子存下 callback_url，有结果时 requests.post(callback_url, json=result)
```

**Unity 端**：

```csharp
// 1. 绑定，上报自己的 IP 和端口
// POST http://192.168.3.126:8080/api/bind
// body: {"device_id":"unity-001","callback_url":"http://192.168.1.50:9000/result"}

// 2. 本地起 HTTP 监听，等板子回调
var listener = new HttpListener();
listener.Prefixes.Add("http://+:9000/result/");
listener.Start();
```

- **优点**：板子可以主动推
- **缺点**：Unity 需要起 HTTP Server，NAT 穿透麻烦，Unity 设备 IP 可能变化

适合：局域网内，Unity 设备 IP 固定

---

### 方案 C：WebSocket 长连接（推荐）

绑定 = Unity 连上板子的 WebSocket，连接本身就是绑定，断了就是解绑，板子不需要存任何 IP。

```
Unity ──ws://192.168.3.126:8080/ws──▶ 板子（建立连接 = 绑定）
板子有结果 ──push──▶ Unity（通过已建立的连接）
```

**板子端**（`web_server.py` 新增 WebSocket endpoint）：

```python
# 使用 websockets 或 Flask-SocketIO
# 客户端连上后记录连接句柄
# 有结果时 await ws.send(json.dumps(result))
```

**Unity 端**（使用 NativeWebSocket 或 WebSocketSharp）：

```csharp
var ws = new WebSocket("ws://192.168.3.126:8080/ws");
ws.OnMessage += (sender, e) => {
    var result = JsonUtility.FromJson<TaskResult>(e.Data);
    Debug.Log($"板子推送：{result}");
};
ws.Connect();
```

- **优点**：板子随时推，Unity 不需要起 Server，不需要知道对方 IP
- **缺点**：需要在板子的 web_server.py 里加 WebSocket 支持

适合：需要实时推送结果的场景（语音任务完成、状态变化等）

---

### 方案 D：MQTT Broker 中转

双方都连同一个 MQTT Broker（局域网内任意一台机器）：

```
板子 ──publish──▶ Broker ──▶ Unity（subscriber）
Unity ──publish──▶ Broker ──▶ 板子（subscriber）
```

- 谁都不需要知道对方 IP，只需要知道 Broker IP
- 板子已有 `mqtt_client.py`，这条路是现成的
- **缺点**：多一个 Broker 进程要维护

适合：多设备场景，或已有 MQTT 基础设施

---

## 选型建议

| 需求 | 推荐方案 |
|------|----------|
| Unity 主动下发任务，板子同步返回 | 方案 A（RunCommand） |
| 板子执行完主动通知 Unity | 方案 C（WebSocket） |
| 多块板子 + 多个 Unity 设备 | 方案 D（MQTT） |
| 局域网简单双向通信 | 方案 C（WebSocket） |

**当前最省事的路径**：

1. 任务下发继续用 `sshreceiver.py`（`RunCommand`）
2. 结果推送加一个 WebSocket endpoint，Unity 订阅

---

## 注意事项

- 方案 A/C 都要求 Unity 设备和板子在同一局域网
- 方案 B 中 Unity 设备的 IP 如果变化（DHCP），需要重新绑定
- WebSocket 断线后需要在 Unity 端实现重连逻辑
- 板子 IP 固定为 `192.168.3.126`，如果 IP 变化需要更新配置
