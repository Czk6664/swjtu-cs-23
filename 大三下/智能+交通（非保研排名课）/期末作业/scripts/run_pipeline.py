"""演示一次端到端决策请求：路由→小模型→采集→融合→决策与解释。

用法:
    python scripts/run_pipeline.py            # 跑内置三个典型场景
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capstone.pipeline import TrafficDecisionSystem  # noqa: E402

SCENES = [
    {"scene_id": "S1-高峰路口", "workflow": "intersection-risk", "traffic_load": 0.85,
     "forecast_dataset": "PEMS08",
     "detections": [{"cls": "pl40", "conf": 0.42}, {"cls": "pn", "conf": 0.31}],
     "query": "这个路口高峰期需要注意什么管制？"},
    {"scene_id": "S2-平峰路段", "workflow": "congestion", "traffic_load": 0.2,
     "forecast_dataset": "PEMS08", "query": "当前路段拥堵风险如何？"},
    {"scene_id": "S3-仅检测低置信", "workflow": "sign-only",
     "detections": [{"cls": "pl100", "conf": 0.18}]},
]


def main():
    sys_ = TrafficDecisionSystem()
    for scene in SCENES:
        r = sys_.decision_flow(scene)
        print("=" * 72)
        print(f"场景 {r.scene_id}")
        print(f"  风险等级 : {r.risk_level} (score={r.risk_score})")
        print(f"  建议动作 : {r.action}")
        print(f"  结构理由 : {r.rationale}")
        if r.contributions:
            print("  信号贡献 :")
            for c in r.contributions:
                print(f"    - {c['signal']:10s} risk={c['risk']:<5} conf={c['confidence']:<5} "
                      f"贡献={c['contribution']}")
        if r.disagreements:
            print(f"  协同分歧 : {r.disagreements}")
    print("=" * 72)
    print("遥测已落盘到 data/telemetry/，可运行 scripts/simulate_flywheel.py 跑飞轮。")


if __name__ == "__main__":
    main()
