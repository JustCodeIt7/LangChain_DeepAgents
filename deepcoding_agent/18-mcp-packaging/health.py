"""
Startup checks: fail with an explanation, not a traceback.
==========================================================
The two things that actually go wrong on a fresh machine are "Ollama is not
running" and "that model is not pulled". Both produce confusing errors deep
inside the HTTP client, so we check for them up front and say what to do.
"""

import json
import urllib.error
import urllib.request

import config

OLLAMA_URL = "http://localhost:11434"


def check() -> str | None:
    """Return a human-readable problem, or None if everything looks fine.

    Only Ollama is checked: for any other provider the model string points at
    a cloud API, and a missing key surfaces clearly on the first request.
    """
    if not config.MODEL.startswith("ollama:"):
        return None

    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2) as response:
            installed = {model["name"] for model in json.load(response).get("models", [])}
    except (urllib.error.URLError, TimeoutError, OSError):
        return (
            f"**Ollama is not reachable** at {OLLAMA_URL}.\n\n"
            "Start it with `ollama serve`, or set `DEEPCODER_MODEL` to a cloud "
            "model such as `openai:gpt-5.5`."
        )

    wanted = config.MODEL.removeprefix("ollama:")
    # Ollama reports "name:tag"; a bare name means the ":latest" tag.
    if wanted not in installed and f"{wanted}:latest" not in installed:
        return (
            f"**Model `{wanted}` is not pulled.**\n\n"
            f"Run `ollama pull {wanted}`, or pick one you already have:\n"
            + "\n".join(f"- `{name}`" for name in sorted(installed)[:8])
        )
    return None
