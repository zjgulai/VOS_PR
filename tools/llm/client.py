"""
tools/llm/client.py — Kimi + DeepSeek 统一 LLM 调用入口

是什么：封装 Kimi（moonshot）和 DeepSeek API，提供统一的 complete() 接口
输入：prompt 文本 + 任务类型
输出：str（LLM 生成文本）
不是什么：不做缓存，不做重试（由调用方决定）

API 兼容性（已确认）：
  Kimi：   base_url=https://api.moonshot.cn/v1，兼容 OpenAI SDK
  DeepSeek: base_url=https://api.deepseek.com，兼容 OpenAI SDK

快速测试：
    python3 tools/llm/client.py --provider kimi --prompt "用一句话描述母婴行业"
    python3 tools/llm/client.py --provider deepseek --prompt "用一句话描述母婴行业"

环境变量（在部署服务器设置）：
    export KIMI_API_KEY="your-kimi-key"
    export DEEPSEEK_API_KEY="your-deepseek-key"
"""
from __future__ import annotations

import os

import re as _re
def _load_zshrc_keys():
    zshrc = os.path.expanduser("~/.zshrc")
    try:
        content = open(zshrc).read()
        for m in _re.finditer(r'export (\w+API\w*)="([^"]+)"', content):
            key, val = m.group(1), m.group(2)
            if not os.environ.get(key):
                os.environ[key] = val
    except Exception:
        pass
_load_zshrc_keys()
import sys
from typing import Optional

sys.path.insert(0, str(__import__('pathlib').Path.home() / "Library/Python/3.9/lib/python/site-packages"))


PROVIDER_CONFIG = {
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "env_key": "KIMI_API_KEY",
        "default_model": "moonshot-v1-32k",
        "long_model": "moonshot-v1-128k",
        "max_tokens": 4096,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "reasoning_model": "deepseek-reasoner",
        "max_tokens": 4096,
    },
}

TASK_ROUTING = {
    "summarize_article": "kimi",
    "generate_report":   "kimi",
    "score_risk":        "deepseek",
    "identify_opportunity": "deepseek",
    "extract_entities":  "kimi",
    "classify_sentiment":"deepseek",
}


def _get_client(provider: str):
    cfg = PROVIDER_CONFIG.get(provider)
    if not cfg:
        raise ValueError(f"Unknown provider: {provider}. Choose: {list(PROVIDER_CONFIG)}")

    api_key = os.environ.get(cfg["env_key"])
    if not api_key:
        raise EnvironmentError(
            f"{cfg['env_key']} not set. "
            f"Run: export {cfg['env_key']}='your-key'"
        )

    try:
        import openai
    except ImportError:
        raise ImportError("openai not installed. Run: pip install openai --user")

    return openai.OpenAI(base_url=cfg["base_url"], api_key=api_key), cfg


def complete(
    prompt: str,
    task_type: Optional[str] = None,
    provider: Optional[str] = None,
    system_prompt: Optional[str] = None,
    use_long_context: bool = False,
) -> str:
    if provider is None:
        provider = TASK_ROUTING.get(task_type or "", "kimi")

    client, cfg = _get_client(provider)

    model = cfg["long_model"] if use_long_context and "long_model" in cfg \
            else cfg["default_model"]

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=cfg["max_tokens"],
        temperature=0.3,
    )
    return response.choices[0].message.content or ""


def check_availability() -> dict:
    results = {}
    for provider in PROVIDER_CONFIG:
        cfg = PROVIDER_CONFIG[provider]
        api_key = os.environ.get(cfg["env_key"])
        if not api_key:
            results[provider] = {"available": False, "reason": f"{cfg['env_key']} not set"}
            continue
        try:
            client, _ = _get_client(provider)
            r = client.chat.completions.create(
                model=cfg["default_model"],
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            results[provider] = {"available": True, "model": cfg["default_model"]}
        except Exception as e:
            results[provider] = {"available": False, "reason": str(e)[:100]}
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["kimi", "deepseek", "auto"], default="auto")
    parser.add_argument("--prompt", required=False, default="Hello, 用中文回复我一句话")
    parser.add_argument("--check", action="store_true", help="检查 API Key 可用性")
    args = parser.parse_args()

    if args.check:
        print("检查 LLM API 可用性...")
        results = check_availability()
        for p, r in results.items():
            status = "✓ 可用" if r["available"] else f"✗ 不可用: {r.get('reason','')}"
            print(f"  {p}: {status}")
    else:
        provider = None if args.provider == "auto" else args.provider
        try:
            result = complete(args.prompt, provider=provider)
            print(f"[{provider or 'auto'}] {result}")
        except EnvironmentError as e:
            print(f"✗ {e}")
            print("  提示：在部署服务器上设置环境变量后再运行")
