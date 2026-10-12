param(
    [string]$EnvName = "sr-course-design"
)

$ErrorActionPreference = "Stop"

conda run -n $EnvName python -m src.smoke_test_ms
conda run -n $EnvName python -m pytest tests/test_losses.py tests/test_models.py tests/test_dataset.py tests/test_infer_smoke.py tests/test_metrics.py -q
