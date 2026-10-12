"""配置加载 + 路径解析。复用大作业3 的 Config 风格，但聚焦本系统的阈值/路径。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]   # .../期末作业
WORKSPACE_ROOT = PROJECT_ROOT.parent                  # .../智能交通

_DEFAULTS: dict[str, Any] = {
    # 决策融合阈值
    "fusion": {
        "risk_high": 0.66,
        "risk_medium": 0.33,
        # 各信号对总风险的权重
        "weights": {"forecast": 0.5, "detection": 0.35, "knowledge": 0.15},
    },
    # 数据飞轮
    "flywheel": {
        "mining": {
            "det_conf_threshold": 0.35,     # 检测置信低于此 → 难例
            "forecast_mae_sigma": 2.0,      # 预测误差超过滚动基线 + k·σ → 难例
            "min_hard_cases_to_retrain": 5, # 累积难例达到才触发重训
        },
        "promotion": {
            # 候选必须在主指标上优于生产，且安全子集不回归
            "min_primary_gain": 0.005,      # 主指标最小提升
            "max_safety_regression": 0.0,   # 安全子集允许的最大回退(0=不许回退)
        },
    },
    # 大模型 provider：复用大作业3 的 travelqa LLM(默认 offline，不下载模型)
    "llm": {"provider": "offline"},
    "paths": {
        "data_dir": "data",
        # 小模型产物（相对 workspace root）
        "forecast_results": "大作业1/results",
        "detection_yaml": "大作业2/traffic_sign_detection/configs/dataset/tt100k.yaml",
        "detection_csv": "大作业2/exp_C_704_b8_w0_e50/exp_C_704_b8_w0_e50/results.csv",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        out[k] = _deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


@dataclass
class Config:
    data: dict[str, Any] = field(default_factory=lambda: dict(_DEFAULTS))

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        cfg = dict(_DEFAULTS)
        for cand in ([path] if path else [PROJECT_ROOT / "configs" / "thresholds.yaml"]):
            if cand and Path(cand).exists():
                try:
                    import yaml
                    loaded = yaml.safe_load(Path(cand).read_text(encoding="utf-8")) or {}
                    cfg = _deep_merge(cfg, loaded)
                except ModuleNotFoundError:
                    pass
                break
        return cls(cfg)

    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.data
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    def workspace_path(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (WORKSPACE_ROOT / p)

    def data_path(self, *parts: str) -> Path:
        return PROJECT_ROOT / self.get("paths", "data_dir", default="data") / Path(*parts)
