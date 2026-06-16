# 蓝牙收发说明

当前工程同时保留两种蓝牙通道。

## 经典蓝牙 RFCOMM

代码文件：

- `bt_client.py`

用途：

- Android、Windows、Linux 可用的蓝牙串口。
- 底层设备为 `/dev/rfcomm0`。
- 数据格式为 UTF-8 文本，一行一条消息。

收包规则：

```text
JSON 对象 + \n -> 原样作为任务/命令
普通文本 + \n -> {"type":"command","command":"文本"}
```

示例：

```text
status
```

等价于：

```json
{"type":"command","command":"status"}
```

## BLE UART

代码文件：

- `ble_uart_dbus.py`
- `ble_uart_start.sh`

用途：

- iPhone 蓝牙调试助手可用。
- 通过 BlueZ D-Bus 注册 GATT Server。
- 使用 Nordic UART Service UUID。

UUID：

```text
Service: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
RX 写入: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
TX 通知: 6E400003-B5A3-F393-E0A9-E50E24DCCA9E
```

iPhone 使用方式：

1. 扫描 `student-rk3506js-001`
2. 连接设备
3. 对 TX 特征开启 notify
4. 向 RX 特征写入文本或 JSON

当前 TX notify 会周期性发送状态：

```json
{"type":"status","state":"connecting","message":"waiting bluetooth","timestamp":1781431991}
```

向 RX 写入：

```text
status
```

会通过 TX 返回：

```json
{"type":"command_result","command":"status","status":{...}}
```

## 公共协议模块

代码文件：

- `bluetooth_protocol.py`

职责：

- 统一 NUS UUID。
- 统一 JSON 行编码。
- 统一普通文本/JSON 的解析。
- 统一 BLE RX 记录、状态读取和心跳 payload。

后续如果要把 BLE RX 真正接入主业务，只需要让 `ble_uart_dbus.py` 把解析后的消息投递给 `main.py` 的任务队列或一个本地 IPC 即可。
