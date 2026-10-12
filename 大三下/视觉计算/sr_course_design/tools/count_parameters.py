"""Count trainable parameters for supported SR models."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.imdn import CAIMDN, IDBIMDN, IMDN
from src.models.srcnn import SRCNN


def count_params(model) -> int:
    total = 0
    for parameter in model.trainable_params():
        size = 1
        for dim in parameter.shape:
            size *= dim
        total += size
    return total


def main() -> None:
    rows = [
        {"model": "SRCNN", "params": count_params(SRCNN(scale=2))},
        {"model": "IMDN width16 depth4", "params": count_params(IMDN(scale=2, num_features=16, num_blocks=4))},
        {"model": "IMDN width32 depth2", "params": count_params(IMDN(scale=2, num_features=32, num_blocks=2))},
        {"model": "IMDN width32 depth4", "params": count_params(IMDN(scale=2, num_features=32, num_blocks=4))},
        {"model": "IMDN width32 depth6", "params": count_params(IMDN(scale=2, num_features=32, num_blocks=6))},
        {"model": "IMDN width48 depth4", "params": count_params(IMDN(scale=2, num_features=48, num_blocks=4))},
        {"model": "IDB-IMDN-Lite width32 depth4", "params": count_params(IDBIMDN(scale=2, num_features=32, num_blocks=4))},
        {"model": "CA-IMDN width32 depth4", "params": count_params(CAIMDN(scale=2, num_features=32, num_blocks=4))},
    ]
    output = PROJECT_ROOT / "results" / "summaries" / "parameter_counts.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["model", "params"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved parameter counts: {output}")


if __name__ == "__main__":
    main()
