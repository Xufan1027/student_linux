# ESP32-S3 到 RK3506JS Linux 替换关系

## 迁移原则

- 原 ESP32-S3 工程只作为业务逻辑参考。
- Linux 代码全部放在 `student_linux/`。
- 当前 RK3506JS 无屏幕，显示模块只保留日志接口。
- 优先使用 Python、Bluetooth、WebSocket、ALSA `arecord/aplay`；MQTT 保留为备用模式。

## 模块替换表

| ESP32-S3 原逻辑 | RK3506JS Linux 替换 |
| --- | --- |
| `app_main()` | `main.py` |
| FreeRTOS queue/task/timer | Python 主循环、回调、后续可用线程或 `asyncio` |
| `sdkconfig` / Kconfig | `config.json` |
| NVS 配置存储 | `config.json` 文件 |
| `esp_wifi` STA/AP 配网 | Linux 系统网络，程序只检查连接 |
| 本地 HTTP 配置页面 | 暂不迁移，先用 `config.json` |
| 教师端任务传输 | 默认 Bluetooth SPP/RFCOMM JSON 行协议 |
| ESP-IDF MQTT 组件 | `paho-mqtt` 备用 |
| `esp_websocket_client` | `websocket-client`，后续可换 `websockets` |
| FunASR WebSocket 协议 | `ws_client.py` |
| chatAgent WebSocket 协议 | `ws_client.py` |
| I2S + ES8388/ES8311 codec | ALSA `arecord` / `aplay` |
| `audio_capture_task()` | `audio_record.py` |
| `playback_task()` | `audio_play.py` |
| LVGL/OLED/SPI LCD | `display.py` 日志输出 |
| BOOT/KEY GPIO | `button.py` 占位接口 |
| ESP32 状态变量 | `device_state.py` |
| `servo_pwm` | 暂不迁移 |

## 已完成内容

- 已创建 Linux 工程目录和指定文件。
- 已写入默认 `config.json`。
- 已创建蓝牙、MQTT 备用、WebSocket、音频、显示、按键、状态、启动脚本和 systemd 服务文件骨架。
- 第三阶段已实现基础业务链路：蓝牙收任务、arecord raw PCM 流式录音、FunASR WebSocket 流式识别、chatAgent WebSocket 流式接收、aplay stdin 流式播放、蓝牙发结果。
- 已优化运行时目录到 `/userdata/student/`，状态、结果、录音缓存和日志不再写入工程目录。
- 已增加蓝牙断开后自动重新等待连接。
- 已增加蓝牙/网页共用文本命令：`status`、`play_test`、`record_test`、`restart`。
- 已增加轻量网页端：`http://板子IP:8080/`。
- 已增强 Buildroot init 脚本：启动前记录版本、IP、蓝牙和声卡信息；异常退出后自动重启。

## 模块测试命令

配置读取：

```sh
cd /opt/student_linux
python3 main.py
```

依赖安装：

```sh
python3 -m pip install -r requirements.txt
```

蓝牙准备：

```sh
python3 main.py --bluetooth-prepare
```

蓝牙常驻服务：

```sh
python3 main.py
```

蓝牙任务 JSON，发送时加换行：

```json
{"task_id":"bt-demo","type":"voice_answer","prompt":"请回答问题","record_seconds":5}
```

MQTT 备用连接测试：

```sh
python3 mqtt_client.py --config config.json
```

MQTT 常驻收任务：

```sh
python3 mqtt_client.py --config config.json --listen
```

录音测试：

```sh
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/student_test.wav
python3 audio_record.py --config config.json --output /tmp/student_test.wav
```

播放测试：

```sh
aplay -D hw:0,0 /tmp/student_test.wav
python3 audio_play.py --config config.json /tmp/student_test.wav
```

WebSocket 连通性测试：

```sh
python3 ws_client.py --config config.json --check both
```

FunASR 文件识别测试：

```sh
python3 ws_client.py --config config.json --check funasr --transcribe /tmp/student_test.wav
```

chatAgent 文本问答测试：

```sh
python3 ws_client.py --config config.json --check agent --ask "你好"
```

完整本地假任务测试，不连接蓝牙：

```sh
python3 main.py --once
```

完整蓝牙服务：

```sh
python3 main.py
```

整段文件备用模式：

```sh
python3 main.py --file-mode
```

完整 MQTT 备用服务：

```sh
python3 main.py --mqtt
```

网页端测试：

```sh
curl http://127.0.0.1:8080/api/status
curl http://127.0.0.1:8080/api/log
curl -X POST http://127.0.0.1:8080/api/command -d '{"command":"status"}'
curl -X POST http://127.0.0.1:8080/api/command -d '{"command":"play_test"}'
curl -X POST http://127.0.0.1:8080/api/command -d '{"command":"record_test"}'
```

运行时文件检查：

```sh
ls -lh /userdata/student
cat /userdata/student/status.json
tail -f /userdata/student/student.log
tail -f /userdata/student/results.jsonl
```
