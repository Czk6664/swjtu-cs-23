from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable



def copy_report_figures(paths: Iterable[Path], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        destination = output_dir / path.name
        shutil.copy2(path, destination)
