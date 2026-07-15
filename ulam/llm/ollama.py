from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Iterable

from .base import LLMClient
from .http import extract_ollama_content, ollama_chat_endpoints, urlopen_read
from .prompt import build_prompt, parse_tactics
from .runtime import run_with_runtime_controls
from ..types import ProofState


class OllamaClient(LLMClient):
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_s: float | None = 60.0,
        heartbeat_s: float | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
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
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        endpoints = ollama_chat_endpoints(self._base_url)
        last_error: Exception | None = None
        for url in endpoints:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            try:
                raw = run_with_runtime_controls(
                    lambda req=req: urlopen_read(req, self._timeout_s),
                    timeout_s=self._timeout_s,
                    heartbeat_s=self._heartbeat_s,
                )
                content = extract_ollama_content(raw)
                if not content:
                    raise RuntimeError("Ollama response missing content")
                return parse_tactics(content, k)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code in (404, 405):
                    continue
                raise
        if last_error:
            raise last_error
        raise RuntimeError("Ollama response missing content")
