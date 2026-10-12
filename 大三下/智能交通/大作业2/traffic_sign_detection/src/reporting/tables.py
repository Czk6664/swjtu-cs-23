from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd



def metrics_to_dataframe(metrics: Dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame([{"metric": key, "value": value} for key, value in metrics.items()])



def save_markdown_table(metrics: Dict[str, float], output_path: Path) -> None:
    dataframe = metrics_to_dataframe(metrics)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dataframe.to_markdown(index=False), encoding="utf-8")
