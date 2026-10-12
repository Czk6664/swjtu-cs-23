"""遥测采集：每次推理/决策落一行到 Parquet（按 模型/日期 分区）。

字段对齐 design.md 4.4。pyarrow 可用时写 Parquet；否则回退 JSONL，保证可跑。
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_FIELDS = ["inference_id", "model_name", "model_version", "ts", "input_ref",
           "output", "confidence", "ground_truth_ref", "big_model_verdict",
           "flagged_reason"]


class TelemetryCollector:
    def __init__(self, telemetry_dir: Path):
        self.dir = Path(telemetry_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def log(self, model_name: str, model_version: str, output: dict,
            confidence: float, input_ref: str = "", ground_truth_ref: str = "",
            big_model_verdict: dict | None = None, flagged_reason: str = "") -> dict:
        row = {
            "inference_id": str(uuid.uuid4()),
            "model_name": model_name,
            "model_version": model_version,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "input_ref": input_ref,
            "output": json.dumps(output, ensure_ascii=False),
            "confidence": float(confidence),
            "ground_truth_ref": ground_truth_ref,
            "big_model_verdict": json.dumps(big_model_verdict or {}, ensure_ascii=False),
            "flagged_reason": flagged_reason,
        }
        self._append(model_name, row)
        return row

    def _partition(self, model_name: str) -> Path:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        p = self.dir / f"model={model_name}" / f"date={date}"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _append(self, model_name: str, row: dict) -> None:
        part = self._partition(model_name)
        try:
            import pandas as pd  # noqa
            f = part / "part.parquet"
            df_new = pd.DataFrame([row], columns=_FIELDS)
            if f.exists():
                df = pd.concat([pd.read_parquet(f), df_new], ignore_index=True)
            else:
                df = df_new
            df.to_parquet(f, index=False)
        except ModuleNotFoundError:
            with (part / "part.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def read_all(self, model_name: str | None = None):
        """读回遥测为 list[dict]（pandas 优先，回退 JSONL）。"""
        rows: list[dict] = []
        roots = ([self.dir / f"model={model_name}"] if model_name
                 else list(self.dir.glob("model=*")))
        for root in roots:
            if not root.exists():
                continue
            for f in root.rglob("part.parquet"):
                try:
                    import pandas as pd
                    rows.extend(pd.read_parquet(f).to_dict("records"))
                except ModuleNotFoundError:
                    pass
            for f in root.rglob("part.jsonl"):
                rows.extend(json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l)
        return rows
