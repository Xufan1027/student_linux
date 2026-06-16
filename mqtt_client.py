import argparse
import json
import time
from typing import Callable, Optional

try:
    import paho.mqtt.client as mqtt
except ModuleNotFoundError:
    mqtt = None


class StudentMqttClient:
    def __init__(self, config: dict, on_task: Optional[Callable[[dict], None]] = None):
        if mqtt is None:
            raise RuntimeError("Missing dependency: install paho-mqtt with `python3 -m pip install -r requirements.txt`")
        self.config = config
        self.mqtt_cfg = config["mqtt"]
        self.on_task = on_task
        self.connected = False
        self.client = self._create_client(config["device"]["device_id"])
        username = self.mqtt_cfg.get("username")
        password = self.mqtt_cfg.get("password")
        if username:
            self.client.username_pw_set(username, password or None)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    @staticmethod
    def _create_client(client_id: str):
        try:
            return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
        except AttributeError:
            return mqtt.Client(client_id=client_id)

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = rc == 0
        if rc == 0:
            task_topic = self.mqtt_cfg["topics"]["task"]
            client.subscribe(task_topic, qos=1)
            print(f"MQTT connected, subscribed: {task_topic}", flush=True)
            self.publish_status({"state": "online", "message": "mqtt connected"})
        else:
            print(f"MQTT connect failed: rc={rc}", flush=True)

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"MQTT disconnected: rc={rc}", flush=True)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as exc:
            print(f"Invalid MQTT task payload: {exc}", flush=True)
            return
        if self.on_task:
            self.on_task(payload)

    def connect(self) -> None:
        self.client.connect(
            self.mqtt_cfg["host"],
            int(self.mqtt_cfg.get("port", 1883)),
            int(self.mqtt_cfg.get("keepalive", 60)),
        )

    def loop_start(self) -> None:
        self.client.loop_start()

    def loop_forever(self) -> None:
        self.client.loop_forever()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def publish_status(self, payload: dict) -> None:
        self._publish(self.mqtt_cfg["topics"]["status"], payload)

    def publish_result(self, payload: dict) -> None:
        self._publish(self.mqtt_cfg["topics"]["result"], payload)

    def _publish(self, topic: str, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False)
        self.client.publish(topic, body, qos=1)
        print(f"MQTT publish {topic}: {body}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Test MQTT connection and publish a status packet.")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--listen", action="store_true", help="Keep running and print incoming tasks.")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as fp:
        config = json.load(fp)

    def on_task(task: dict) -> None:
        print(f"MQTT task: {json.dumps(task, ensure_ascii=False)}", flush=True)

    client = StudentMqttClient(config, on_task=on_task)
    client.connect()
    if args.listen:
        client.loop_forever()
    else:
        client.loop_start()
        time.sleep(2)
        client.publish_status({"state": "test", "message": "mqtt module test", "timestamp": int(time.time())})
        time.sleep(1)
        client.stop()


if __name__ == "__main__":
    main()
