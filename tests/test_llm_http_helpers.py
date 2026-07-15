from __future__ import annotations

import json

from ulam.llm.http import (
    ensure_cmd,
    extract_anthropic_content,
    extract_ollama_content,
    extract_openai_content,
    ollama_chat_endpoints,
)


def test_extract_openai_content_from_message() -> None:
    raw = json.dumps({"choices": [{"message": {"content": "hello"}}]})
    assert extract_openai_content(raw) == "hello"


def test_extract_openai_content_from_text_field() -> None:
    raw = json.dumps({"choices": [{"text": "hello-text"}]})
    assert extract_openai_content(raw) == "hello-text"


def test_extract_openai_content_missing_choices_returns_empty() -> None:
    assert extract_openai_content(json.dumps({})) == ""
    assert extract_openai_content(json.dumps({"choices": []})) == ""


def test_extract_anthropic_content_from_content_list() -> None:
    raw = json.dumps(
        {"content": [{"type": "text", "text": "part1"}, {"type": "text", "text": "part2"}]}
    )
    assert extract_anthropic_content(raw) == "part1\npart2"


def test_extract_anthropic_content_ignores_non_text_blocks() -> None:
    raw = json.dumps({"content": [{"type": "image", "text": "ignored"}]})
    assert extract_anthropic_content(raw) == ""


def test_extract_anthropic_content_fallback_text_field() -> None:
    raw = json.dumps({"text": "fallback"})
    assert extract_anthropic_content(raw) == "fallback"


def test_extract_ollama_content_from_message() -> None:
    raw = json.dumps({"message": {"content": "chat-style"}})
    assert extract_ollama_content(raw) == "chat-style"


def test_extract_ollama_content_from_choices() -> None:
    raw = json.dumps({"choices": [{"message": {"content": "openai-style"}}]})
    assert extract_ollama_content(raw) == "openai-style"


def test_extract_ollama_content_from_response_field() -> None:
    raw = json.dumps({"response": "generate-style"})
    assert extract_ollama_content(raw) == "generate-style"


def test_extract_ollama_content_missing_returns_empty() -> None:
    assert extract_ollama_content(json.dumps({})) == ""


def test_ollama_chat_endpoints_plain_base_url() -> None:
    endpoints = ollama_chat_endpoints("http://localhost:11434")
    assert endpoints == [
        "http://localhost:11434/api/chat",
        "http://localhost:11434/v1/chat/completions",
    ]


def test_ollama_chat_endpoints_strips_api_suffix() -> None:
    endpoints = ollama_chat_endpoints("http://localhost:11434/api")
    assert endpoints == [
        "http://localhost:11434/api/chat",
        "http://localhost:11434/v1/chat/completions",
    ]


def test_ollama_chat_endpoints_v1_base_url_dedupes() -> None:
    endpoints = ollama_chat_endpoints("http://localhost:11434/v1")
    assert endpoints == [
        "http://localhost:11434/v1/chat/completions",
        "http://localhost:11434/api/chat",
    ]
    assert len(endpoints) == len(set(endpoints))


def test_ensure_cmd_raises_for_missing_binary() -> None:
    import pytest

    with pytest.raises(RuntimeError):
        ensure_cmd("definitely-not-a-real-binary-xyz")


def test_ensure_cmd_passes_for_existing_binary() -> None:
    ensure_cmd("python3")
