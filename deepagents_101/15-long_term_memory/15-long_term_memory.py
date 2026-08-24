"""
15 - Long-Term Memory Across Conversations
==========================================
- Episode 12's checkpointer remembers ONE thread; a store remembers ALL of them
- Route /memories/ to a `StoreBackend` so files outlive the conversation
- `memory=[...]` loads those files into the system prompt on every run

Run:  python 15-long_term_memory.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from dotenv import load_dotenv
from langgraph.store.memory import InMemoryStore  # dev store; swap for Postgres
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: A store, and a namespace to file things under
# `namespace` is a CALLABLE receiving the run's Runtime, so real deployments can
# scope memory per user, e.g. lambda rt: (rt.server_info.user.identity,).
# Locally there is no user, so we pin everything to one bucket.
store = InMemoryStore()
memory_backend = StoreBackend(store=store, namespace=lambda runtime: ("demo-user",))

# %% Step 3: Mount the store at /memories/
# Everything else stays virtual and disappears when the run ends — only the
# /memories/ path is persistent.
backend = CompositeBackend(
    default=StateBackend(),
    routes={"/memories/": memory_backend},
)

MEMORY_FILE = "/memories/preferences.md"

agent = create_deep_agent(
    model=MODEL,
    backend=backend,
    memory=[MEMORY_FILE],  # loaded into the system prompt at the start of each run
    system_prompt=(
        "You are a personal assistant. When the user states a durable "
        f"preference, save it by writing to {MEMORY_FILE}. Reply in one sentence."
    ),
)


def say(text: str, thread_id: str) -> str:
    """Send one message on a named thread and return the reply."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": text}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return text_of(result["messages"][-1]).strip()


# %% Step 4: Teach it something on thread one
first_turn = "I'm vegetarian - always remember that. Save it to your memory file."
print("[bold cyan]Conversation 1 (thread 'monday'):[/bold cyan]")
print(f"  [dim]user:[/dim]  {first_turn}")
print(f"  [green]agent:[/green] {say(first_turn, 'monday')}")

# %% Step 5: Look at what actually got stored
# The file is now in the store, completely outside any conversation history.
print("\n[bold cyan]Contents of the store:[/bold cyan]")
for item in store.search(("demo-user",)):
    body = str(item.value.get("content", "")).strip().replace("\n", " ")
    print(f"  [yellow]{item.key}[/yellow]: {body[:100]}")

# %% Step 6: Start a BRAND NEW conversation and check recall
# Different thread_id = no shared message history (see ep. 12). Anything the
# agent knows here came from the memory file, not the conversation.
print("\n[bold cyan]Conversation 2 (thread 'friday' — no shared history):[/bold cyan]")
print("  [dim]user:[/dim]  Suggest a dinner for me.")
print(f"  [green]agent:[/green] {say('Suggest a dinner for me.', 'friday')}")

# %%
