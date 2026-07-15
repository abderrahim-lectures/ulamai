from __future__ import annotations

import time


def call_gemini(
    api_key: str,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.2,
    max_output_tokens: int = 256,
    max_retries: int = 3,
    backoff_s: float = 2.0,
) -> str:
    """Call Gemini via the official google-genai SDK, with retry/backoff on
    transient server errors (e.g. 503 "high demand") that the raw HTTP shim
    this used to go through had no protection against.
    """
    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=model, contents=user, config=config)
            return response.text or ""
        except errors.ServerError as exc:
            last_error = exc
            if attempt < max_retries - 1:
                time.sleep(backoff_s * (attempt + 1))
    raise RuntimeError(f"Gemini request failed after {max_retries} attempts: {last_error}") from last_error
