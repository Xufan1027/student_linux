# SSH Receiver 使用说明

`sshreceiver.py` 是学生端工程里的 SSH 消息入口，用来从电脑向 RK3506JS 板子发送一次命令或任务。

它不是常驻服务。它每运行一次，只接收一条消息，然后把消息写入板子上的任务队列文件：

```text
/userdata/student/ble_tasks.jsonl
```

主程序 `main.py` 会后台轮询这个文件，把新消息取出来执行。

## 适用场景

- 不想用 MQTT 时，从电脑直接控制板子。
- 蓝牙还没调通时，用 SSH 临时下发任务。
- 想快速测试 `status`、`record_test`、`play_test`、语音任务流程。
- 远程帮别人调板子，只要能 SSH 登录即可。

## 基本命令

板子地址：

```text
192.168.3.126
```

登录用户：

```text
root
```

密码：

```text
root
```

在电脑上执行：

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py status'
```

这条命令会向板子发送 `status` 命令。

## 支持的消息格式

### 1. 普通文本命令

如果发送的内容不是 JSON，`sshreceiver.py` 会把它当作命令：

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py status'
```

等价于写入：

```json
{"type":"command","command":"status"}
```

### 2. JSON 命令

也可以直接发送 JSON：

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py '\''{"type":"command","command":"record_test"}'\'''
```

### 3. JSON 任务

发送完整语音任务：

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py '\''{"task_id":"ssh-demo","type":"voice_answer","prompt":"请回答问题","record_seconds":5}'\'''
```

## 常用命令和效果

### 查询状态

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py status'
```

效果：

- 写入一条 `status` 命令。
- `main.py` 读取后返回当前设备状态。
- 状态会更新到网页端。

网页查看：

```text
http://192.168.3.126:8080/
```

### 录音测试

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py record_test'
```

效果：

- 板子调用 `arecord` 录音。
- 生成或覆盖最近录音文件。
- 网页端“录音文件”区域可以播放或下载。

录音文件位置：

```text
/userdata/student/last_record.wav
```

### 播放测试音频

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py play_test'
```

效果：

- 板子调用 `aplay` 播放测试音频。
- 用于检查喇叭、声卡、音频配置是否正常。

### 重启学生端主程序

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py restart'
```

效果：

- 主程序收到重启命令后退出。
- `S99student` 启动脚本会自动拉起主程序。

### 下发语音问答任务

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py '\''{"task_id":"ssh-voice-001","type":"voice_answer","prompt":"请回答老师的问题","record_seconds":5}'\'''
```

效果：

- 板子进入录音或流式监听流程。
- 调用 ASR 识别学生语音。
- 调用 AI WebSocket 生成回复。
- 调用 TTS/音频播放流程。
- 最终结果写入：

```text
/userdata/student/results.jsonl
```

网页端“最近结果”会显示执行结果。

## 从 stdin 发送

如果命令太长，也可以用管道：

```sh
echo '{"task_id":"stdin-demo","type":"voice_answer","prompt":"测试 stdin 任务","record_seconds":5}' | \
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py'
```

## 只解析不入队

调试消息格式时，可以加 `--no-enqueue`。这样只打印解析结果，不写入任务队列，也不会触发主程序执行：

```sh
ssh root@192.168.3.126 'cd /opt/student_linux && python3 sshreceiver.py --no-enqueue status'
```

输出示例：

```json
{"type":"command","command":"status"}
```

## 查看是否写入成功

在板子上查看任务队列：

```sh
tail -n 20 /userdata/student/ble_tasks.jsonl
```

查看学生端日志：

```sh
tail -f /userdata/student/student.log
```

查看结果：

```sh
tail -n 20 /userdata/student/results.jsonl
```

## 和 BLE 的关系

`sshreceiver.py` 写入的队列文件和 BLE 任务队列共用：

```text
/userdata/student/ble_tasks.jsonl
```

所以从 SSH 发任务、从 BLE 发任务，最后都会进入 `main.py` 的同一套业务流程。

当前推荐理解方式：

```text
电脑 SSH 命令
  -> sshreceiver.py
  -> /userdata/student/ble_tasks.jsonl
  -> main.py 后台轮询
  -> 执行命令或语音任务
  -> 网页状态 / 日志 / results.jsonl
```

## 注意事项

- SSH 方式要求电脑和板子网络互通。
- 如果板子 IP 变化，需要把命令里的 `192.168.3.126` 改成新的 IP。
- `record_test` 和语音任务会占用麦克风。
- `play_test` 和 TTS 播放会占用扬声器。
- `restart` 会让网页端短暂断开，几秒后自动恢复。
- 如果 ASR、AI、TTS 服务器不可用，语音任务可能会失败，但 `status`、`record_test`、`play_test` 仍可用于本地测试。
