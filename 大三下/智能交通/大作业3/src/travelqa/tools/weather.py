"""天气工具。

mock provider 用确定性示例数据跑通离线原型；amap provider 调用高德 Web 服务
天气查询 API。密钥仅从环境变量读取，避免提交到仓库。
"""
from __future__ import annotations

from typing import Any

AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"


def weather_query(cfg, city: str = "成都", date: str = "今天") -> dict:
    provider = cfg.get("tools", "weather", "provider", default="mock")
    if provider in {"amap", "api"}:
        return _amap_weather(cfg, city, date)
    return _mock_weather(city, date)


def _mock_weather(city: str, date: str) -> dict:
    return {
        "source": "mock",
        "available": True,
        "city": city,
        "date": date,
        "condition": "小雨转多云",
        "temp_range_c": [18, 24],
        "wind": "东北风 3 级",
        "advice": "有降雨，路面湿滑，建议预留出行时间、保持车距并开启近光灯。",
    }


def _amap_weather(cfg, city: str, date: str) -> dict:
    import requests

    key_env = cfg.get("tools", "weather", "api_key_env", default="TRAVELQA_AMAP_KEY")
    key = cfg.secret(key_env)
    if not key:
        return _failed(city, date, f"缺少环境变量 {key_env}")

    adcode = str(cfg.get("tools", "weather", "adcode", default="510100"))
    extensions = "base" if date in {"今天", "今日", "现在"} else "all"
    base = cfg.get("tools", "weather", "api_base", default=AMAP_WEATHER_URL)
    try:
        resp = requests.get(
            base,
            params={"city": adcode, "extensions": extensions, "key": key},
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != "1":
            return _failed(city, date, payload.get("info", "高德天气 API 返回失败"))
        if extensions == "base":
            return _live_weather(city, date, payload)
        return _forecast_weather(city, date, payload)
    except (requests.RequestException, ValueError) as exc:
        return _failed(city, date, f"高德天气 API 请求失败: {exc}")


def _live_weather(city: str, date: str, payload: dict[str, Any]) -> dict:
    lives = payload.get("lives") or []
    if not lives:
        return _failed(city, date, "高德天气 API 未返回实时天气")
    item = lives[0]
    return {
        "source": "amap",
        "available": True,
        "city": item.get("city", city),
        "adcode": item.get("adcode", ""),
        "date": date,
        "condition": item.get("weather", ""),
        "temperature_c": item.get("temperature", ""),
        "humidity_pct": item.get("humidity", ""),
        "wind": f"{item.get('winddirection', '')}风 {item.get('windpower', '')}级",
        "reported_at": item.get("reporttime", ""),
    }


def _forecast_weather(city: str, date: str, payload: dict[str, Any]) -> dict:
    forecasts = payload.get("forecasts") or []
    casts = forecasts[0].get("casts", []) if forecasts else []
    if not casts:
        return _failed(city, date, "高德天气 API 未返回预报")
    offset = {"明天": 1, "后天": 2}.get(date, 0)
    item = casts[min(offset, len(casts) - 1)]
    return {
        "source": "amap",
        "available": True,
        "city": forecasts[0].get("city", city),
        "adcode": forecasts[0].get("adcode", ""),
        "date": date,
        "forecast_date": item.get("date", ""),
        "day_condition": item.get("dayweather", ""),
        "night_condition": item.get("nightweather", ""),
        "temperature_range_c": [item.get("nighttemp", ""), item.get("daytemp", "")],
        "day_wind": f"{item.get('daywind', '')}风 {item.get('daypower', '')}级",
        "night_wind": f"{item.get('nightwind', '')}风 {item.get('nightpower', '')}级",
        "reported_at": forecasts[0].get("reporttime", ""),
    }


def _failed(city: str, date: str, error: str) -> dict:
    return {
        "source": "amap",
        "available": False,
        "city": city,
        "date": date,
        "error": error,
    }
