"""启动决策系统 Web 服务: python scripts/serve.py -> http://127.0.0.1:8002"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn  # noqa: E402


def main():
    uvicorn.run("capstone.api:app", host="127.0.0.1", port=8002, reload=False)


if __name__ == "__main__":
    main()
