"""
03 - Adding Your Own Tools
==========================
- Two ways to write a tool: a plain function, or the `@tool` decorator
- The docstring IS the tool description the model reads — write it for the model
- Custom tools are ADDITIVE: you keep every built-in tool as well

Run:  python 03-custom_tools.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_core.tools import tool  # decorator form for tools
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:9b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: A tool can be a plain Python function
# deepagents inspects the signature and docstring to build the tool schema.
# Keep parameter types simple (str/int/bool) — smaller models coerce them better.
def word_count(text: str) -> int:
    """Count how many words are in the given text.

    Args:
        text: The text whose words should be counted.
    """
    return len(text.split())


# %% Step 3: ...or use the @tool decorator
# Same result, but the decorator gives you explicit control (custom name,
# args schema, return_direct, etc.) and turns it into a real BaseTool object.
@tool
def reverse_text(text: str) -> str:
    """Reverse the characters of the given text.

    Args:
        text: The text to reverse.
    """
    return text[::-1]


# %% Step 4: Hand both tools to the agent
# `tools=` ADDS to the built-in suite — it never removes ls/read_file/task/etc.
agent = create_deep_agent(
    model=MODEL,
    tools=[word_count, reverse_text],
    system_prompt=(
        "You are a text utility assistant. Use the reverse_text and word_count "
        "tools to answer. Do not use any filesystem tools."
    ),
)

# %% Step 5: Run a task that needs BOTH tools
task = (
    "Reverse the text 'deep agents are fun', then tell me how many words "
    "the original text has. Use your tools for both steps."
)
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

# %% Step 6: Inspect which tools the agent actually called
print("[bold cyan]Tool calls made:[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        print(f"  [green]{call['name']}[/green]({call['args']})")

print("\n[bold cyan]Tool results:[/bold cyan]")
for message in result["messages"]:
    if message.__class__.__name__ == "ToolMessage":
        print(f"  [yellow]{message.name}[/yellow] -> {text_of(message)}")

print(f"\n[bold green]Final answer:[/bold green] {text_of(result['messages'][-1])}")

# %%
