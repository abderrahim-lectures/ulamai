from __future__ import annotations

from typing import Iterable

from .base import LLMClient
from .http import ensure_cmd
from .prompt import build_prompt, parse_tactics
from .cli_utils import claude_print
from ..types import ProofState


class ClaudeCLIClient(LLMClient):
    def __init__(
        self,
        model: str | None = None,
        timeout_s: float | None = None,
        heartbeat_s: float | None = None,
    ) -> None:
        self._model = model
        self._timeout_s = timeout_s
        self._heartbeat_s = heartbeat_s
        ensure_cmd("claude")

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
        text = claude_print(
            system,
            user,
            model=self._model,
            timeout_s=self._timeout_s,
            heartbeat_s=self._heartbeat_s,
        )
        return parse_tactics(text, k)
