"""Test the real Amap weather and route tools without starting the Web app."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from travelqa.config import Config  # noqa: E402
from travelqa.tools import route_plan, weather_query  # noqa: E402


def main() -> None:
    cfg = Config.load()
    cfg.data.setdefault("tools", {}).setdefault("weather", {})["provider"] = "amap"
    cfg.data.setdefault("tools", {}).setdefault("route", {})["provider"] = "amap"
    print("=== Amap weather ===")
    print(json.dumps(weather_query(cfg, city="成都", date="今天"), ensure_ascii=False, indent=2))
    print("\n=== Amap driving route ===")
    print(json.dumps(route_plan(cfg, "成都东站", "春熙路", mode="drive"),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
