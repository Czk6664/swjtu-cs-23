"""重训触发与候选生成。

⚠ 按"模型先不下载"约束：本模块**不真正训练**，而是按"策展样本量 → 指标提升"的
   确定性模型**模拟**出候选版本的指标，用于演示飞轮闭环、门控与回滚（与 design.md
   第6节的飞轮实验方案一致）。接入真实重训时，把 _simulate_metrics 换成调用
   大作业1/大作业2 的训练脚本(复用根 WSL-Hermes 异步任务承载长任务)即可，接口不变。
"""
from __future__ import annotations

PRIMARY = {"forecast": "mae", "detection": "mAP50"}   # 主指标
# 主指标方向：mAP 越大越好，mae 越小越好
_HIGHER_BETTER = {"mAP50": True, "mae": False}


def retrain_candidate(model_name: str, base_metrics: dict, num_curated: int,
                      next_version: str, inject_regression: bool = False) -> dict:
    """返回候选版本的 metrics + checkpoint 占位。"""
    metrics = _simulate_metrics(model_name, base_metrics, num_curated, inject_regression)
    return {
        "version": next_version,
        "checkpoint": f"runs/{model_name}/{next_version}/best.pt",   # 占位路径
        "metrics": metrics,
        "num_curated": num_curated,
        "simulated": True,
    }


def _simulate_metrics(model_name: str, base: dict, n: int, regress: bool) -> dict:
    primary = PRIMARY.get(model_name, "mAP50")
    higher = _HIGHER_BETTER.get(primary, True)
    cur = float(base.get(primary, 0.7 if higher else 13.0))

    # 提升幅度：随策展样本量递增、边际递减
    gain_ratio = min(0.12, 0.02 * (n ** 0.5))
    if regress:    # 故意制造劣化候选，演示门控拦截
        gain_ratio = -0.05

    if higher:     # 如 mAP50：向 1.0 靠拢
        new = cur + gain_ratio * (1.0 - cur)
    else:          # 如 mae：向 0 靠拢（减小）
        new = cur * (1.0 - gain_ratio)

    out = dict(base)
    out[primary] = round(new, 4)
    return out
