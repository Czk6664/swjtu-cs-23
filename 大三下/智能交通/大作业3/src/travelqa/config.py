"""配置加载。优先级: 环境变量 > config.yaml > config.example.yaml > 内置默认值。

设计原则:
- 原型默认全离线，缺失配置文件也能跑（用内置默认）。
- 密钥永远不写进 yaml，只从环境变量读取（见 security 规则）。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../大作业3

_DEFAULTS: dict[str, Any] = {
    "llm": {"provider": "offline", "base_url": "", "api_key": "",
            "model": "deepseek-llm-7b-chat"},
    "embedding": {"provider": "offline_hash", "model": "BAAI/bge-small-zh-v1.5", "dim": 512},
    "retrieval": {"mode": "hybrid", "top_k": 4, "min_score": 0.05,
                  "rerank_top_k": 4,
                  "reranker": {"provider": "offline", "model": "BAAI/bge-reranker-v2-m3"}},
    "tools": {
        "weather": {"provider": "mock",
                    "api_base": "https://restapi.amap.com/v3/weather/weatherInfo",
                    "api_key_env": "TRAVELQA_AMAP_KEY",
                    "adcode": "510100"},
        "route": {"provider": "mock", "api_key_env": "TRAVELQA_AMAP_KEY",
                  "city": "成都", "adcode": "510100"},
    },
    "integrations": {
        "forecast": {"enabled": True, "results_dir": "../大作业1/results"},
        "detection": {"enabled": True,
                      "dataset_yaml": "../大作业2/traffic_sign_detection/configs/dataset/tt100k.yaml",
                      "run_csv": "../大作业2/exp_C_704_b8_w0_e50/exp_C_704_b8_w0_e50/results.csv"},
    },
    "paths": {"raw_dir": "data/raw", "kb_dir": "data/kb"},
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


@dataclass
class Config:
    data: dict[str, Any] = field(default_factory=lambda: dict(_DEFAULTS))

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        cfg = dict(_DEFAULTS)
        candidates = [path] if path else [
            PROJECT_ROOT / "config.yaml",
            PROJECT_ROOT / "config.example.yaml",
        ]
        for cand in candidates:
            if cand and Path(cand).exists():
                loaded = _read_yaml(Path(cand))
                if loaded:
                    cfg = _deep_merge(cfg, loaded)
                break
        return cls(cfg)

    # 便捷访问 ----------------------------------------------------------------
    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.data
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    def resolve_path(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (PROJECT_ROOT / p)

    def secret(self, env_var: str) -> str:
        return os.environ.get(env_var, "") or _read_local_secret(env_var)


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ModuleNotFoundError:
        # 没装 pyyaml 也别炸，原型继续用默认值
        return {}


def _read_local_secret(name: str) -> str:
    """Read an ignored project-local secret file as an offline convenience."""
    path = PROJECT_ROOT / ".env.local"
    if not path.exists():
        return ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip("\"'")
    return ""
