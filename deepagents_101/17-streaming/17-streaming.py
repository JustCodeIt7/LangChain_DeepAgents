"""
17 - Streaming
==============
- `stream_mode="updates"`: one chunk per graph step — great for progress UIs
- `stream_mode="messages"`: token-by-token output — great for chat UIs
- `subgraphs=True` also surfaces what SUBAGENTS are doing

Run:  python 17-streaming.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


# %% Step 2: A tool so there is something to watch besides text
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: The first number.
        b: The second number.
    """
    return a + b


agent = create_deep_agent(
    model=MODEL,
    tools=[add],
    system_prompt="You are a math helper. Use the add tool, then state the result.",
)

QUESTION = "What is 128 plus 349? Use the add tool."

# %% Step 3: Mode 1 — "updates": what just happened, step by step
# Each chunk is {node_name: state_update}. This is what you render as
# "Thinking...", "Calling add...", "Done" in a progress indicator.
print("[bold cyan]stream_mode='updates' — one chunk per step:[/bold cyan]")
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": QUESTION}]}, stream_mode="updates"
):
    for node_name, update in chunk.items():
        details = ""
        if isinstance(update, dict):
            for message in update.get("messages", []):
                calls = getattr(message, "tool_calls", []) or []
                if calls:
                    details = f" -> called {', '.join(c['name'] for c in calls)}"
        print(f"  [magenta]{node_name}[/magenta]{details}")

# %% Step 4: Mode 2 — "messages": tokens as the model produces them
# NOTE the shape: this mode yields (message_chunk, metadata) TUPLES, not plain
# chunks. Unpacking it wrong is the most common streaming bug.
print("\n[bold cyan]stream_mode='messages' — live tokens:[/bold cyan]")
print("  ", end="")
for message_chunk, metadata in agent.stream(
    {"messages": [{"role": "user", "content": QUESTION}]}, stream_mode="messages"
):
    # This mode emits EVERY message, including tool results. Filter to just the
    # assistant's own tokens, and drop internal machinery like summarization,
    # so the user sees only the answer they asked for.
    if metadata.get("lc_source") == "summarization":
        continue
    if message_chunk.__class__.__name__ != "AIMessageChunk":
        continue
    content = message_chunk.content
    if isinstance(content, list):  # OpenAI-style content blocks
        content = "".join(b.get("text", "") for b in content if isinstance(b, dict))
    if content:
        print(content, end="")
print()

# %% Step 5: Seeing inside subagents
# By default a subagent's internal steps are hidden from the stream. Pass
# subgraphs=True and each chunk arrives as (namespace_tuple, chunk) — the
# namespace tells you WHICH subagent produced it:
#
#   for namespace, chunk in agent.stream(payload, stream_mode="updates",
#                                        subgraphs=True):
#       print(namespace, chunk)
#
# Combine that with episode 09's subagents to build a UI that shows each
# delegated task progressing independently.
print("\n[dim]Tip: add subgraphs=True to also stream subagent internals.[/dim]")

# %%
