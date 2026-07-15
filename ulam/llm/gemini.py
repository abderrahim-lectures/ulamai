from __future__ import annotations

from typing import Iterable

from .base import LLMClient
from .gemini_client import call_gemini
from .prompt import build_prompt, parse_tactics
from .runtime import run_with_runtime_controls
from ..types import ProofState


class GeminiClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai",
        model: str = "gemini-3.1-pro-preview",
        temperature: float = 0.2,
        timeout_s: float | None = 60.0,
        heartbeat_s: float | None = None,
    ) -> None:
        if not api_key:
            raise RuntimeError("Gemini API key is required.")
        self._api_key = api_key
        # base_url is unused by the official google-genai SDK (it talks to
        # Google's endpoint directly); kept for config/API back-compat.
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
        content = run_with_runtime_controls(
            lambda: call_gemini(
                self._api_key, self._model, system, user, temperature=self._temperature
            ),
            timeout_s=self._timeout_s,
            heartbeat_s=self._heartbeat_s,
        )
        if not content:
            raise RuntimeError("Gemini response missing content")
        return parse_tactics(content, k)
