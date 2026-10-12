"""启动出行问答 Web 服务: python scripts/serve.py  -> http://127.0.0.1:8001"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn  # noqa: E402


def main():
    uvicorn.run("travelqa.api:app", host="127.0.0.1", port=8001, reload=False)


if __name__ == "__main__":
    main()
