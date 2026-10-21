"""演示: 命令行问答。覆盖全部要求功能 + 高阶集成。

用法:
    python scripts/chat.py                 # 交互式
    python scripts/chat.py --demo          # 跑一组预设问题，演示六类意图
    python scripts/chat.py -q "成都限行怎么规定的"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from travelqa.app import TravelQAApp  # noqa: E402

DEMO_QUESTIONS = [
    "成都市的尾号限行是怎么规定的？",        # 交管信息 (RAG)
    "下雨天开车需要注意什么？",              # 出行建议 (RAG)
    "成都今天天气怎么样，适合开车吗？",       # 天气
    "我从天府广场到春熙路怎么走？",          # 路径规划
    "PEMS08 上交通流预测的精度如何？",       # 高阶: 大作业1
    "这个系统能识别哪些交通标志，准确率多少？", # 高阶: 大作业2
]


def show(app, q):
    ans = app.ask(q)
    print(f"\n问: {q}")
    print(f"[意图] {ans.intent}")
    print(ans.text)
    if ans.sources:
        print("来源:", "; ".join(f"{s['title']}({s['fetched_at']})" for s in ans.sources))
    print("-" * 70)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("-q", "--question")
    args = ap.parse_args()

    app = TravelQAApp()
    if not app.retriever.ready():
        print("[!] 知识库为空，请先运行: python scripts/2_build_kb.py")

    if args.question:
        show(app, args.question)
    elif args.demo:
        for q in DEMO_QUESTIONS:
            show(app, q)
    else:
        print("智能交通出行问答 (输入 quit 退出)")
        while True:
            try:
                q = input("\n你: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in {"quit", "exit", "q", ""}:
                break
            show(app, q)


if __name__ == "__main__":
    main()
