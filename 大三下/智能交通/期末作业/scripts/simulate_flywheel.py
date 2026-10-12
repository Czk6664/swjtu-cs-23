"""演示数据飞轮闭环（design.md 第6节实验）：

1. 灌入若干带难例的遥测（模拟系统在线运行积累数据）。
2. 连续跑 N 轮飞轮，打印 detection mAP50 随轮次的提升曲线。
3. 故意注入一个劣化候选，演示门控拦截 + 保留生产版本（可回滚）。

注意：按"模型先不下载"，重训为确定性模拟（见 flywheel/trainer.py），
      用于演示闭环/门控/回滚机制，而非真实训练。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capstone.config import Config                       # noqa: E402
from capstone.flywheel import TelemetryCollector         # noqa: E402
from capstone.pipeline import TrafficDecisionSystem      # noqa: E402

MODEL = "detection"


def seed_hard_cases(cfg, n=8):
    """灌入低置信检测遥测作为难例。"""
    col = TelemetryCollector(cfg.data_path("telemetry"))
    for i in range(n):
        col.log(model_name=MODEL, model_version="v1",
                output={"cls": "pl100", "conf": 0.18}, confidence=0.18,
                input_ref=f"seed-{i}", flagged_reason="low_confidence(<0.35)")


def main():
    cfg = Config.load()
    sys_ = TrafficDecisionSystem(cfg)

    print(f"初始生产版本 mAP50 = {sys_.registry.production_metrics(MODEL, 'mAP50')}")
    seed_hard_cases(cfg, n=8)

    print("\n--- 连续飞轮轮次（正常重训）---")
    for rnd in range(1, 4):
        rep = sys_.flywheel_round(MODEL)
        prod = sys_.registry.production_metrics(MODEL, "mAP50")
        print(f"第{rnd}轮: 难例={rep['hard_cases']} 状态={rep['status']} "
              f"候选mAP50={rep.get('candidate_metrics', {}).get('mAP50')} "
              f"→ 生产mAP50={prod}")
        if rep["status"] == "promoted":
            seed_hard_cases(cfg, n=8)   # 继续积累，驱动下一轮

    print("\n--- 注入劣化候选（演示门控拦截 + 可回滚）---")
    seed_hard_cases(cfg, n=8)
    before = sys_.registry.production_metrics(MODEL, "mAP50")
    rep = sys_.flywheel_round(MODEL, inject_regression=True)
    after = sys_.registry.production_metrics(MODEL, "mAP50")
    print(f"候选mAP50={rep.get('candidate_metrics', {}).get('mAP50')} "
          f"门控={'通过' if rep['gate']['passed'] else '拦截'}: {rep['gate']['reason']}")
    print(f"生产版本 mAP50: {before} → {after}（劣化候选未上线，生产保持不变）")

    print("\n注册表版本：", list(sys_.registry.list_versions(MODEL).keys()),
          "当前生产=", sys_.registry.production_version(MODEL))


if __name__ == "__main__":
    main()
