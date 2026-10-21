import argparse
import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


def build_payload(device_id: str, seq: int) -> dict:
    return {
        "device_id": device_id,
        "seq": seq,
        "temperature": round(random.uniform(21.0, 32.0), 2),
        "humidity": round(random.uniform(35.0, 75.0), 2),
        "voltage": round(random.uniform(3.55, 4.2), 3),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Simulate an edge sensor publishing telemetry through MQTT.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--device-id", default="edge-k3s-node-01")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    args = parser.parse_args()

    topic = f"edge/sensors/{args.device_id}/telemetry"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{args.device_id}-publisher")
    client.connect(args.host, args.port, keepalive=30)
    client.loop_start()

    for seq in range(1, args.count + 1):
        payload = build_payload(args.device_id, seq)
        text = json.dumps(payload, ensure_ascii=False)
        result = client.publish(topic, text, qos=args.qos)
        result.wait_for_publish()
        print(f"[edge] published topic={topic} payload={text}", flush=True)
        time.sleep(args.interval)

    client.loop_stop()
    client.disconnect()
    print("[edge] finished", flush=True)


if __name__ == "__main__":
    main()
