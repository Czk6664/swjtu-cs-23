import json
import os
import signal
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import redis


MQTT_HOST = os.getenv("MQTT_HOST", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "edge/sensors/#")
REDIS_HOST = os.getenv("REDIS_HOST", "redis-svc")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
REDIS_STREAM = os.getenv("REDIS_STREAM", "edge:sensor:stream")
REDIS_LATEST_PREFIX = os.getenv("REDIS_LATEST_PREFIX", "edge:sensor:latest:")

running = True
rds = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
)


def stop(_signum, _frame):
    global running
    running = False


def on_connect(client, _userdata, _flags, reason_code, _properties=None):
    print(f"[gateway] connected to MQTT {MQTT_HOST}:{MQTT_PORT}, reason={reason_code}", flush=True)
    client.subscribe(MQTT_TOPIC, qos=1)
    print(f"[gateway] subscribed topic={MQTT_TOPIC}", flush=True)


def on_message(_client, _userdata, message):
    received_at = datetime.now(timezone.utc).isoformat()
    raw = message.payload.decode("utf-8", errors="replace")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {"raw": raw}

    device_id = str(payload.get("device_id", "unknown"))
    record = {
        "topic": message.topic,
        "device_id": device_id,
        "payload": json.dumps(payload, ensure_ascii=False),
        "received_at": received_at,
        "qos": str(message.qos),
    }
    rds.xadd(REDIS_STREAM, record, maxlen=1000, approximate=True)
    rds.set(f"{REDIS_LATEST_PREFIX}{device_id}", record["payload"], ex=3600)
    print(f"[gateway] stored topic={message.topic} device={device_id} payload={record['payload']}", flush=True)


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    rds.ping()
    print(f"[gateway] redis ready at {REDIS_HOST}:{REDIS_PORT}", flush=True)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="cloud-mqtt-redis-gateway")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()

    while running:
        time.sleep(1)

    client.loop_stop()
    client.disconnect()
    print("[gateway] stopped", flush=True)


if __name__ == "__main__":
    main()
