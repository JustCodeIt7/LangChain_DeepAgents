"""
12 - Memory Within a Conversation (Checkpointers & Threads)
===========================================================
- A checkpointer saves state after every step, so turn 2 remembers turn 1
- A `thread_id` names the conversation; same id = same history
- Different thread_id = a completely separate conversation

Run:  python 12-checkpointer_threads.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver  # dev checkpointer
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:9b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: Add a checkpointer
# InMemorySaver keeps history in RAM — great for demos and tests. Swap in
# SqliteSaver or PostgresSaver for something that survives a restart.
agent = create_deep_agent(
    model=MODEL,
    checkpointer=InMemorySaver(),
    system_prompt="You are a friendly assistant. Reply in one short sentence.",
)


def say(text: str, thread_id: str) -> str:
    """Send one message on a named thread and return the reply."""
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": text}]}, config=config
    )
    return text_of(result["messages"][-1]).strip()


# %% Step 3: Two turns on the SAME thread
# The second invoke passes no history — the checkpointer reloads it from
# thread "alice". This is what makes a real chat loop possible.
print("[bold cyan]Thread 'alice':[/bold cyan]")
print("  [dim]user:[/dim]  My favorite number is 42.")
print(f"  [green]agent:[/green] {say('My favorite number is 42.', 'alice')}")
print("  [dim]user:[/dim]  What is my favorite number?")
print(f"  [green]agent:[/green] {say('What is my favorite number?', 'alice')}")

# %% Step 4: The same question on a DIFFERENT thread
# Thread "bob" has its own history, which is empty — so the agent has no idea.
# This isolation is how one deployment serves many users safely.
print("\n[bold cyan]Thread 'bob' (a separate conversation):[/bold cyan]")
print("  [dim]user:[/dim]  What is my favorite number?")
print(f"  [green]agent:[/green] {say('What is my favorite number?', 'bob')}")

# %% Step 5: Inspect the stored history
# get_state() lets you read back whatever the checkpointer holds for a thread.
print("\n[bold cyan]Messages stored per thread:[/bold cyan]")
for thread_id in ("alice", "bob"):
    snapshot = agent.get_state({"configurable": {"thread_id": thread_id}})
    print(f"  [yellow]{thread_id}[/yellow]: {len(snapshot.values['messages'])} messages")

# %%
