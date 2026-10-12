"""出行路径规划工具。

mock provider 返回离线示例；amap provider 先将地点名称解析为经纬度，再调用
高德 Web 服务路径规划 API。真实模式失败时不回退到 mock，避免伪造实时耗时。
"""
from __future__ import annotations

import re
from typing import Any

AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
AMAP_PLACE_TEXT_URL = "https://restapi.amap.com/v3/place/text"
AMAP_ROUTE_URLS = {
    "drive": "https://restapi.amap.com/v3/direction/driving",
    "transit": "https://restapi.amap.com/v3/direction/transit/integrated",
    "walk": "https://restapi.amap.com/v3/direction/walking",
}


def route_plan(cfg, origin: str, destination: str, mode: str = "drive") -> dict:
    provider = cfg.get("tools", "route", "provider", default="mock")
    if provider == "amap":
        return _amap_route(cfg, origin, destination, mode)
    return _mock_route(origin, destination, mode)


def _mock_route(origin: str, destination: str, mode: str) -> dict:
    plans = {
        "drive": {"distance_km": 12.4, "duration_min": 35,
                  "summary": "经天府大道-人民南路，高峰期约 35 分钟",
                  "note": "若为尾号限行日且车辆受限，建议改乘地铁。"},
        "transit": {"distance_km": 13.1, "duration_min": 42,
                    "summary": "地铁1号线转3号线，全程约 42 分钟，步行接驳约 8 分钟"},
        "walk": {"distance_km": 1.2, "duration_min": 16, "summary": "步行约 16 分钟"},
    }
    return {
        "source": "mock", "available": True, "origin": origin, "destination": destination,
        "mode": mode, "plan": plans.get(mode, plans["drive"]),
        "alternatives": [m for m in plans if m != mode],
    }


def _amap_route(cfg, origin: str, destination: str, mode: str) -> dict:
    import requests

    key_env = cfg.get("tools", "route", "api_key_env", default="TRAVELQA_AMAP_KEY")
    key = cfg.secret(key_env)
    if not key:
        return _failed(origin, destination, mode, f"缺少环境变量 {key_env}")
    if mode not in AMAP_ROUTE_URLS:
        return _failed(origin, destination, mode, f"不支持的出行方式: {mode}")
    if origin in {"当前位置", ""} or destination in {"目的地", ""}:
        return _failed(origin, destination, mode, "未能从问题中提取完整起点和终点")

    city = cfg.get("tools", "route", "city", default="成都")
    adcode = str(cfg.get("tools", "route", "adcode", default="510100"))
    try:
        origin_location = _resolve_location(requests, key, city, adcode, origin)
        destination_location = _resolve_location(requests, key, city, adcode, destination)
        params = {
            "origin": origin_location,
            "destination": destination_location,
            "key": key,
            "extensions": "base",
        }
        if mode == "transit":
            params.update({"city": city, "cityd": city})
        payload = _amap_get(requests, AMAP_ROUTE_URLS[mode], params)
        return _route_result(origin, destination, mode, origin_location, destination_location, payload)
    except (requests.RequestException, ValueError) as exc:
        return _failed(origin, destination, mode, f"高德路径规划 API 请求失败: {exc}")


def _resolve_location(requests, key: str, city: str, adcode: str, place: str) -> str:
    if re.fullmatch(r"-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?", place):
        return place
    location = _poi_location(requests, key, adcode, place)
    return location or _geocode(requests, key, city, place)


def _poi_location(requests, key: str, adcode: str, place: str) -> str:
    payload = _amap_get(
        requests,
        AMAP_PLACE_TEXT_URL,
        {
            "keywords": place,
            "city": adcode,
            "citylimit": "true",
            "extensions": "all",
            "offset": "1",
            "page": "1",
            "key": key,
        },
    )
    pois = payload.get("pois") or []
    if not pois:
        return ""
    poi = pois[0]
    entrance = poi.get("entr_location")
    return entrance if isinstance(entrance, str) and entrance else poi.get("location", "")


def _geocode(requests, key: str, city: str, place: str) -> str:
    payload = _amap_get(
        requests,
        AMAP_GEOCODE_URL,
        {"address": place, "city": city, "key": key},
    )
    geocodes = payload.get("geocodes") or []
    if not geocodes or not geocodes[0].get("location"):
        raise ValueError(f"无法解析地点: {place}")
    return geocodes[0]["location"]


def _amap_get(requests, url: str, params: dict[str, str]) -> dict[str, Any]:
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "1":
        raise ValueError(payload.get("info", "高德 API 返回失败"))
    return payload


def _route_result(
    origin: str,
    destination: str,
    mode: str,
    origin_location: str,
    destination_location: str,
    payload: dict[str, Any],
) -> dict:
    route = payload.get("route") or {}
    paths = route.get("paths") or []
    if not paths:
        return _failed(origin, destination, mode, "高德路径规划 API 未返回路线")
    path = paths[0]
    steps = path.get("steps") or []
    instructions = [step.get("instruction", "") for step in steps if step.get("instruction")]
    return {
        "source": "amap",
        "available": True,
        "origin": origin,
        "destination": destination,
        "origin_location": origin_location,
        "destination_location": destination_location,
        "mode": mode,
        "distance_km": _meters_to_km(path.get("distance")),
        "duration_min": _seconds_to_minutes(path.get("duration")),
        "tolls_yuan": path.get("tolls", ""),
        "traffic_lights": path.get("traffic_lights", ""),
        "instructions": instructions[:8],
    }


def _meters_to_km(value: Any) -> float | None:
    try:
        return round(float(value) / 1000, 1)
    except (TypeError, ValueError):
        return None


def _seconds_to_minutes(value: Any) -> int | None:
    try:
        return round(float(value) / 60)
    except (TypeError, ValueError):
        return None


def _failed(origin: str, destination: str, mode: str, error: str) -> dict:
    return {
        "source": "amap",
        "available": False,
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "error": error,
    }
