"""离线评测: 意图路由准确率 + RAG 关键信息命中率。

不依赖大模型(离线 provider 下也能跑)，主要评测系统的『路由 + 检索』骨架质量。
接入真实 DeepSeek 后可再加生成质量(人工评分/LLM-as-judge)。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from travelqa.app import TravelQAApp     # noqa: E402
from travelqa.router import classify     # noqa: E402

EVAL_SET = Path(__file__).resolve().parent / "eval_set.jsonl"


def main():
    cases = [json.loads(l) for l in EVAL_SET.open(encoding="utf-8") if l.strip()]
    app = TravelQAApp()

    intent_ok = 0
    include_total = include_ok = 0
    for c in cases:
        pred = classify(c["query"]).value
        hit = pred == c["expected_intent"]
        intent_ok += hit
        ans = app.ask(c["query"])
        blob = (ans.text + ans.evidence)
        for kw in c.get("must_include", []):
            include_total += 1
            include_ok += kw in blob
        mark = "[OK]" if hit else "[NG]"
        print(f"{mark} [{pred:13s}|期望 {c['expected_intent']:13s}] {c['query']}")

    n = len(cases)
    print("\n=== 评测结果 ===")
    print(f"意图路由准确率 : {intent_ok}/{n} = {intent_ok / n:.1%}")
    if include_total:
        print(f"关键信息命中率 : {include_ok}/{include_total} = {include_ok / include_total:.1%}")


if __name__ == "__main__":
    main()
