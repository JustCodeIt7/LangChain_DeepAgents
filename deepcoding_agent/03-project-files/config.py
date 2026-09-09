"""
Settings for DeepCoder, read once from the environment.
=======================================================
Every knob in the app lives here so no other module calls os.getenv().
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Which model to run. Any LangChain provider string works.
MODEL = os.getenv("DEEPCODER_MODEL", "ollama:qwen3.5:9b")

# The directory the agent is allowed to read and write.
WORKDIR = Path(os.getenv("DEEPCODER_WORKDIR", "./workspace")).resolve()

# How long Ollama keeps the model loaded after a request. The default is 5
# minutes; a coding session has long gaps between turns and reloading a 6 GB
# model from disk takes seconds, so we hold it much longer.
KEEP_ALIVE = os.getenv("DEEPCODER_KEEP_ALIVE", "30m")

# Context window. Ollama's own default is small (often 4096), which a coding
# agent blows through as soon as it reads a couple of files — and it truncates
# SILENTLY, so the agent just seems to "forget". Set it explicitly.
NUM_CTX = int(os.getenv("DEEPCODER_NUM_CTX", "8192"))

SYSTEM_PROMPT = """You are DeepCoder, a terminal coding assistant working in a project directory.

You have filesystem tools. Use them instead of guessing:
- ls / glob / grep to find things
- read_file before you edit or describe a file
- write_file to create, edit_file to change part of an existing file

Answer concisely. Prefer short code examples over long prose.
Paths are relative to the project root."""


def describe() -> str:
    """One-line summary of the active settings, for the startup banner."""
    return f"model: {MODEL}  workdir: {WORKDIR}  ctx: {NUM_CTX}"
