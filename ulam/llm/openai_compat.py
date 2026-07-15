from __future__ import annotations

import json
import urllib.request
from typing import Iterable

from .base import LLMClient
from .http import extract_openai_content, urlopen_read
from .prompt import build_prompt, parse_tactics
from .runtime import run_with_runtime_controls
from ..types import ProofState


class OpenAICompatClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.2,
        timeout_s: float | None = 60.0,
        heartbeat_s: float | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._timeout_s = timeout_s
        self._heartbeat_s = heartbeat_s

    def propose(
        self,
        state: ProofState,
        retrieved: Iterable[str],
        k: int,
        instruction: str | None = None,
        context: Iterable[str] | None = None,
        mode: str = "tactic",
    ) -> list[str]:
        system, user = build_prompt(
            state, retrieved, k, instruction=instruction, context=context, mode=mode
        )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self._temperature,
            "max_tokens": 256,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )
        raw = run_with_runtime_controls(
            lambda: urlopen_read(req, self._timeout_s),
            timeout_s=self._timeout_s,
            heartbeat_s=self._heartbeat_s,
        )
        content = extract_openai_content(raw)
        if not content:
            raise RuntimeError("LLM response missing content")
        return parse_tactics(content, k)
