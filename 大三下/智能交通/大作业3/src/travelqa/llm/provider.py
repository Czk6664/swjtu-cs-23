"""大模型 provider。

- offline           : 不下载模型。基于检索片段 + 工具结果做模板化抽取式应答，
                      让原型端到端可跑通；也作为微调/部署完成前的占位。
- openai_compatible : 接 DeepSeek 官方 API 或本地 vLLM/Ollama 的 OpenAI 兼容接口，
                      微调后把 model 换成你的(合并 LoRA 的)模型名即可。
- ollama_native     : 接本机 Ollama /api/chat，固定 think=false，避免展示推理过程。

统一接口: LLM.generate(system, user) -> str
"""
from __future__ import annotations

from typing import Protocol


class LLM(Protocol):
    def generate(self, system: str, user: str) -> str: ...


class OfflineLLM:
    """离线应答器: 把 system 中已注入的『检索依据/工具结果』整理成可读回答。

    它不做真正的语言生成，而是结构化地复述证据并标注来源，
    保证回答有据可依、可解释——这正是大小模型协同里『大模型负责组织表达』的占位实现。
    """

    def generate(self, system: str, user: str) -> str:
        return (
            "【离线模式应答】\n"
            f"问题: {user}\n\n"
            f"{system.strip()}\n\n"
            "提示: 当前为离线占位回答(未下载/调用大模型)。配置 llm.provider=openai_compatible "
            "并接入微调后的 DeepSeek 模型后，将由大模型基于以上依据生成自然语言回答。"
        )


class OpenAICompatibleLLM:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def generate(self, system: str, user: str) -> str:
        import requests  # 延迟导入
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "temperature": 0.3,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class OllamaNativeLLM:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, system: str, user: str) -> str:
        import requests  # 延迟导入
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "think": False,
                "stream": False,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "options": {"temperature": 0.3},
            },
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


def get_llm(cfg) -> LLM:
    provider = cfg.get("llm", "provider", default="offline")
    if provider == "ollama_native":
        return OllamaNativeLLM(
            base_url=cfg.get("llm", "base_url", default="http://127.0.0.1:11434"),
            model=cfg.get("llm", "model", default="travelqa"),
        )
    if provider == "openai_compatible":
        api_key = cfg.secret("TRAVELQA_LLM_API_KEY") or cfg.get("llm", "api_key", default="")
        return OpenAICompatibleLLM(
            base_url=cfg.get("llm", "base_url", default=""),
            api_key=api_key,
            model=cfg.get("llm", "model", default="deepseek-llm-7b-chat"),
        )
    return OfflineLLM()
