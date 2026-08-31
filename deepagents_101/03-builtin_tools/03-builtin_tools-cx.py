"""
03 - Built-in Tools
==========================
"""

# %% Step 1: Imports and setup
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend  # shell-capable -> unlocks `execute`
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware  # opt-in `write_todos`
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")
