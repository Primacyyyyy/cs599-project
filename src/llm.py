"""DeepSeek 接入层（OpenAI 兼容）。

原仓库直接用 OpenAI；这里改成 DeepSeek，并把调用收敛成两个函数，
方便上层 agent 调用，也方便测试时替换（monkeypatch）。
"""
import json
from .config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        if not settings.DEEPSEEK_API_KEY:
            raise RuntimeError(
                "DEEPSEEK_API_KEY 未设置。请在 .env 中配置后再运行。"
            )
        _client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
    return _client


def chat_json(system: str, user: str, model: str | None = None) -> dict:
    """要求模型返回 JSON 对象并解析。DeepSeek 支持 json_object 输出模式。"""
    resp = _get_client().chat.completions.create(
        model=model or settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )
    return json.loads(resp.choices[0].message.content)


def chat_text(system: str, user: str, model: str | None = None) -> str:
    resp = _get_client().chat.completions.create(
        model=model or settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.9,
    )
    return resp.choices[0].message.content.strip()
