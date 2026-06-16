# RK3506JS Student Linux Client

这是从 ESP32-S3 学生端业务逻辑迁移到 RK3506JS Linux 的独立工程。

当前状态：蓝牙传输 + 流式 ASR/TTS 版。

运行时状态、结果、录音缓存和服务日志默认保存在：

```text
/userdata/student/
```

## 文件说明

- `main.py`：主入口。
- `config.json`：设备、蓝牙、MQTT 备用、WebSocket、音频参数配置。
- `ble_uart_dbus.py`：iPhone 可用的 BLE UART/Nordic UART GATT 服务。
- `bluetooth_pairing_agent.py`：BlueZ 系统蓝牙配对 agent，自动确认 passkey 并信任已配对设备。
- `bluetooth_pairing_agent.sh`：配对 agent 守护启动脚本。
- `bluetooth_protocol.py`：经典蓝牙和 BLE 共用的消息解析、JSON 行编码和 UUID 常量。
- `mqtt_client.py`：MQTT 备用客户端。
- `ws_client.py`：FunASR 与 chatAgent WebSocket 协议骨架。
- `audio_record.py`：`arecord` 录音封装。
- `audio_play.py`：`aplay` 播放封装。
- `display.py`：无屏幕阶段的日志显示接口。
- `button.py`：按键占位接口。
- `device_state.py`：设备状态对象。
- `start.sh`：启动脚本。
- `student.service`：systemd 服务模板。
- `S99student`：Buildroot/BusyBox init 开机自启脚本。
- `PORTING_PLAN.md`：ESP32-S3 到 Linux 的替换关系。
- `BLUETOOTH_PROTOCOL.md`：蓝牙收发协议说明。

## RK3506JS 环境检查命令

```sh
uname -a
cat /etc/os-release
python3 --version
which python3
arecord -l
aplay -l
ip addr
```

## 安装依赖

```sh
python3 -m pip install -r requirements.txt
```

如果开发板没有 pip，先安装系统包或复制离线 wheel 后再安装。

## 运行

```sh
cd /opt/student_linux
./start.sh
```

或者：

```sh
python3 main.py
```

本地假任务测试，不连接蓝牙：

```sh
python3 main.py --once
```

WebSocket 连通性：

```sh
python3 main.py --check-ws both
```

## 音频测试

录音：

```sh
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/student_test.wav
python3 audio_record.py --config config.json --output /tmp/student_test.wav
```

播放：

```sh
aplay -D hw:0,0 /tmp/student_test.wav
python3 audio_play.py --config config.json /tmp/student_test.wav
```

## 蓝牙测试

常驻运行（BLE UART 由 `ble_uart_dbus.py` 独立进程提供）：

```sh
python3 main.py
```

对端连接蓝牙设备名：

```text
student-rk3506js-001
```

iPhone 使用蓝牙调试助手时，请扫描 BLE 设备或 Nordic UART Service。当前启动 BLE UART 广播：

```text
Name: student-rk3506js-001
Service UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
RX Write UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
TX Notify UUID: 6E400003-B5A3-F393-E0A9-E50E24DCCA9E
```

BLE 广播日志：

```sh
tail -f /userdata/student/student.log
ps w | grep bluetoothctl
```

系统蓝牙配对状态检查：

```sh
bluetoothctl show
```

需要看到：

```text
Alias: student-rk3506js-001
Discoverable: yes
Pairable: yes
```

配对时日志里应出现类似：

```text
bluetooth auto-confirm passkey for /org/bluez/hci0/dev_xx_xx_xx_xx_xx_xx: 123456
trusted bluetooth device /org/bluez/hci0/dev_xx_xx_xx_xx_xx_xx
```

如果 iPhone/iPad 之前显示“已拒绝配对”，先在手机蓝牙设置里忽略这个设备，再重启板子服务后重新配对：

```sh
/etc/init.d/S99student restart
```

## MQTT 备用测试

```sh
python3 mqtt_client.py --config config.json
python3 mqtt_client.py --config config.json --listen
```

另一个终端可向任务 topic 发布假任务：

```sh
mosquitto_pub -h 127.0.0.1 -t teacher/tasks/student-rk3506js-001 -m '{"task_id":"demo","type":"voice_answer","prompt":"请回答问题"}'
```

## 网页端

开机服务启动后可访问：

```text
http://192.168.3.126:8080/
```

页面可查看状态、最近日志，也可以触发 `status`、`play_test`、`record_test` 和发送测试任务 JSON。

也可以直接用命令测试：

```sh
curl http://127.0.0.1:8080/api/status
curl http://127.0.0.1:8080/api/log
curl -X POST http://127.0.0.1:8080/api/command -d '{"command":"play_test"}'
curl -X POST http://127.0.0.1:8080/api/command -d '{"command":"record_test"}'
```

## 命令任务

通过 MQTT 任务或网页 `/api/command` 发送的任务，除 JSON 任务外，也可以是一行文本命令：

```text
status
play_test
record_test
restart
```

BLE UART（`ble_uart_dbus.py`）当前只独立应答 `status` 心跳/查询，不会触发完整的录音/识别/AI 任务流程。

## WebSocket 测试

```sh
python3 ws_client.py --config config.json --check both
python3 ws_client.py --config config.json --check funasr --transcribe /tmp/student_test.wav
python3 ws_client.py --config config.json --check agent --ask "你好"
```

## systemd 部署草案

复制工程到开发板：

```sh
scp -r student_linux root@192.168.3.126:/opt/student_linux
```

安装服务：

```sh
cp /opt/student_linux/student.service /etc/systemd/system/student.service
systemctl daemon-reload
systemctl enable student.service
```

启动、停止、重启、查看日志：

```sh
systemctl start student.service
systemctl stop student.service
systemctl restart student.service
journalctl -u student.service -f
```

## Buildroot 开机自启

当前 ATK-DLRK3506JS 镜像使用 BusyBox/init，可用这个方式：

```sh
cp /opt/student_linux/S99student /etc/init.d/S99student
chmod +x /etc/init.d/S99student
/etc/init.d/S99student start
```

停止、重启、查看状态：

```sh
/etc/init.d/S99student stop
/etc/init.d/S99student restart
/etc/init.d/S99student status
tail -f /userdata/student/student.log
```

当前优化版日志路径：

```sh
tail -f /userdata/student/student.log
cat /userdata/student/status.json
tail -f /userdata/student/results.jsonl
```

## 完整流程

```sh
python3 main.py
```

程序会等待蓝牙连接，收到教师端 JSON 任务后录音、识别、请求智能体、播放音频并通过蓝牙发布结果。

默认尽量还原 ESP32-S3 原工程：

```text
arecord raw PCM -> FunASR WebSocket 边录边发
chatAgent audio_base64 -> aplay stdin 边收边播
```

如果需要退回稳妥的整段文件模式：

```sh
python3 main.py --file-mode
```

如果临时需要用 MQTT 备用模式：

```sh
python3 main.py --mqtt
```

## 排查顺序

1. 先运行 `python3 main.py --check-env`。
2. 再测试 `arecord` 和 `aplay`。
3. 再运行 `python3 ws_client.py --config config.json --check both`。
4. 最后运行 `python3 main.py`。
