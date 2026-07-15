from __future__ import annotations

import json
import urllib.request
from shutil import which


def urlopen_read(req: urllib.request.Request, timeout_s: float | None) -> str:
    timeout = timeout_s if timeout_s and timeout_s > 0 else None
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def extract_openai_content(raw: str) -> str:
    data = json.loads(raw)
    choices = data.get("choices") or []
    if not choices:
        return ""
    msg = choices[0]
    if "message" in msg and "content" in msg["message"]:
        return msg["message"]["content"]
    if "text" in msg:
        return msg["text"]
    return ""


def extract_anthropic_content(raw: str) -> str:
    data = json.loads(raw)
    content = data.get("content")
    if isinstance(content, list):
        parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        if parts:
            return "\n".join(parts)
    text = data.get("text", "")
    return text if isinstance(text, str) else ""


def extract_ollama_content(raw: str) -> str:
    data = json.loads(raw)
    message = data.get("message")
    if isinstance(message, dict) and "content" in message:
        return message["content"]
    choices = data.get("choices") or []
    if choices:
        choice = choices[0]
        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"]
        if "text" in choice:
            return choice["text"]
    response = data.get("response")
    return response if isinstance(response, str) else ""


def ollama_chat_endpoints(base_url: str) -> list[str]:
    base = base_url.rstrip("/")
    endpoints: list[str] = []
    if base.endswith("/api"):
        base = base[: -len("/api")]
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
        endpoints.append(f"{base}/v1/chat/completions")
    endpoints.append(f"{base}/api/chat")
    endpoints.append(f"{base}/v1/chat/completions")
    seen: set[str] = set()
    return [url for url in endpoints if not (url in seen or seen.add(url))]


def ensure_cmd(cmd: str) -> None:
    if which(cmd) is None:
        raise RuntimeError(f"{cmd} CLI not found on PATH")
