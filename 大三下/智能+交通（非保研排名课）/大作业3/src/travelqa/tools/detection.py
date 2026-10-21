"""高阶要求 —— 接入大作业2 (YOLO / TT100K 交通目标识别)。

读取大作业2 的数据集类别(tt100k.yaml 的 names)与训练结果(results.csv 末行的
最终 mAP/precision/recall)，支撑『交通目标识别理解问答』:
  - 模型能识别哪些交通标志类别?
  - 检测精度如何(mAP50/mAP50-95)?
  - 某个标志类别(如限速/禁令)的含义?
"""
from __future__ import annotations

import csv
from pathlib import Path

# TT100K 类别前缀语义，便于把 tt100k_plXX 这类编码解释成人话。
_PREFIX_MEANING = {
    "pl": "限速标志(限速值见数字, 如 pl40=限速40)",
    "pn": "禁止驶入/停车类标志",
    "pne": "解除禁止类标志",
    "p": "禁令标志(禁止某种行为)",
    "i": "指示标志(指示行进方向/方式)",
    "w": "警告标志",
}


class DetectionTool:
    def __init__(self, cfg):
        self.enabled = bool(cfg.get("integrations", "detection", "enabled", default=False))
        self.dataset_yaml = cfg.resolve_path(
            cfg.get("integrations", "detection", "dataset_yaml", default=""))
        self.run_csv = cfg.resolve_path(
            cfg.get("integrations", "detection", "run_csv", default=""))

    def available(self) -> bool:
        return self.enabled and Path(self.dataset_yaml).exists()

    def classes(self) -> list[str]:
        path = Path(self.dataset_yaml)
        if not path.exists():
            return []
        names: list[str] = []
        in_names = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("names:"):
                in_names = True
                continue
            if in_names:
                stripped = line.strip()
                if stripped.startswith("- "):
                    names.append(stripped[2:].strip())
                elif stripped and not line.startswith(" "):
                    break  # names 块结束
        return names

    def explain_class(self, name: str) -> str:
        core = name.replace("tt100k_", "")
        for pref in ("pne", "pl", "pn", "p", "i", "w"):
            if core.startswith(pref):
                return f"{name}: {_PREFIX_MEANING.get(pref, '交通标志')}"
        return f"{name}: 交通标志类别"

    def metrics(self) -> dict:
        path = Path(self.run_csv)
        if not path.exists():
            return {"available": False, "reason": f"未找到 {path}"}
        rows = list(csv.reader(path.open(encoding="utf-8")))
        if len(rows) < 2:
            return {"available": False, "reason": "results.csv 无数据行"}
        header = [c.strip() for c in rows[0]]
        last = rows[-1]
        row = dict(zip(header, last))
        return {
            "available": True,
            "epoch": _i(row.get("epoch")),
            "precision": _f(row.get("metrics/precision(B)")),
            "recall": _f(row.get("metrics/recall(B)")),
            "mAP50": _f(row.get("metrics/mAP50(B)")),
            "mAP50_95": _f(row.get("metrics/mAP50-95(B)")),
        }

    def summarize(self) -> dict:
        if not self.available():
            return {"available": False, "reason": "未启用或大作业2 数据集配置不存在"}
        classes = self.classes()
        m = self.metrics()
        parts = (
            f"模型可识别 {len(classes)} 类 TT100K 交通标志; "
            + (f"最终 mAP50={m['mAP50']}, 精确率={m['precision']}, 召回率={m['recall']}。"
               if m.get("available") else "(暂无训练结果)")
        )
        return {"available": True, "num_classes": len(classes),
                "classes": classes, "metrics": m, "interpretation": parts}


def _f(v):
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return v


def _i(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return v
