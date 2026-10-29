"""Optional rewrite pass against any OpenAI-compatible chat endpoint.

Default base_url: http://localhost:11434/v1 (Ollama).
Configuration carries ONLY a base_url - never an API key. If your server
needs auth, run it behind a local proxy; this module deliberately has no
key storage.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .profile import Profile

_SYSTEM_PROMPT = (
    "You are a light-touch copy editor for book back matter. Rewrite the given "
    "text so it sounds like a friendly, plain-English expert talking to a smart "
    "beginner: warm, never condescending, no jargon. Keep every fact, name, "
    "number, URL and meaning exactly as given. Do not add new claims. Keep the "
    "same length and line structure (same number of paragraphs and bullet "
    "lines). Return ONLY the rewritten text."
)


class RewriteError(RuntimeError):
    pass


def _chat(base_url: str, model: str, text: str, temperature: float, timeout: float) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    try:
        return str(body["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RewriteError(f"unexpected response shape from {base_url}: {exc}") from exc


def rewrite_section(section: str, text: str, profile: Profile) -> str:
    """Rewrite one section's text via the configured endpoint.

    Falls back to the original text, returning it unchanged on any error so a
    build never fails because the local model server is down.
    """
    cfg = profile.rewrite
    if not text.strip():
        return text
    try:
        result = _chat(
            cfg["base_url"],
            cfg["model"],
            text,
            cfg["temperature"],
            cfg["timeout"],
        )
    except (RewriteError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"warning: rewrite unavailable for '{section}': {exc}; keeping original")
        return text
    return result or text
