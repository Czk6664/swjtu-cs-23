"""模型版本注册表（data/registry/models.json）。支持晋升与一键回滚。

每个模型: { production: <ver>, versions: { ver: {checkpoint, dataset_snapshot,
            metrics, status, trained_at} } }
status: staging / production / archived
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class ModelRegistry:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._read()

    def _read(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {}

    def _write(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    # 查询 ------------------------------------------------------------------
    def production_metrics(self, model: str, metric: str) -> float | None:
        m = self._data.get(model, {})
        prod = m.get("production")
        if not prod:
            return None
        return m["versions"][prod]["metrics"].get(metric)

    def production_version(self, model: str) -> str | None:
        return self._data.get(model, {}).get("production")

    def list_versions(self, model: str) -> dict:
        return self._data.get(model, {}).get("versions", {})

    # 变更 ------------------------------------------------------------------
    def register(self, model: str, version: str, checkpoint: str,
                 dataset_snapshot: str, metrics: dict, status: str = "staging") -> None:
        m = self._data.setdefault(model, {"production": None, "versions": {}})
        m["versions"][version] = {
            "checkpoint": checkpoint, "dataset_snapshot": dataset_snapshot,
            "metrics": metrics, "status": status,
            "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        if m["production"] is None and status == "production":
            m["production"] = version
        self._write()

    def promote(self, model: str, version: str) -> str | None:
        """把 version 设为 production，旧生产转 archived（保留以便回滚）。返回旧版本。"""
        m = self._data[model]
        old = m.get("production")
        if old and old in m["versions"]:
            m["versions"][old]["status"] = "archived"
        m["versions"][version]["status"] = "production"
        m["production"] = version
        self._write()
        return old

    def rollback(self, model: str, to_version: str) -> None:
        m = self._data[model]
        cur = m.get("production")
        if cur and cur in m["versions"]:
            m["versions"][cur]["status"] = "archived"
        m["versions"][to_version]["status"] = "production"
        m["production"] = to_version
        self._write()
