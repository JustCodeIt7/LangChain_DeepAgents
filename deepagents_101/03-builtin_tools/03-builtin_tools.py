"""
03 - Built-in Tools
==========================

Run:  python 03-builtin_tools.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_core.tools import tool  # decorator form for tools
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")
# %% Step 2: Create the agent with built-in tools
agent = create_deep_agent(
    model=MODEL,
    system_prompt=("You are an assistant with access to built-in tools. Use them to answer user queries efficiently."),
)
