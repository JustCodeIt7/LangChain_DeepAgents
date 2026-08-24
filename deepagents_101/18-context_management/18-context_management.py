"""
18 - Context Management (Summarization)
=======================================
- Long conversations eventually exceed the model's context window
- `SummarizationMiddleware` compresses old turns into a summary automatically
- By default it fires near the context limit; here we force it early to watch it

Run:  python 18-context_management.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:9b")

# %% Step 2: Force summarization to trigger early
# Every deep agent already summarizes automatically, but only near the model's
# context limit (~85%) — impossible to demo cheaply. So we supply our own
# instance with a tiny trigger.
#   trigger = when to summarize      ("messages", 4) -> once history exceeds 4
#   keep    = what to keep verbatim  ("messages", 2) -> the 2 newest messages
#
# Because its `.name` matches the built-in ("SummarizationMiddleware"),
# deepagents REPLACES the default with ours instead of stacking a second one.
summarizer = SummarizationMiddleware(
    model=MODEL,
    trigger=("messages", 4),
    keep=("messages", 2),
)

agent = create_deep_agent(
    model=MODEL,
    middleware=[summarizer],
    checkpointer=InMemorySaver(),  # so all turns share one growing history
    system_prompt="You are a travel assistant. Reply in one short sentence.",
)

CONFIG = {"configurable": {"thread_id": "trip-planning"}}


def turn(text: str) -> int:
    """Send one message and return how many messages the history now holds."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": text}]}, config=CONFIG
    )
    return len(result["messages"])


# %% Step 3: Have a conversation long enough to trip the trigger
# Each exchange adds ~2 messages, so history crosses the limit after a few turns
# and the middleware compresses the older ones.
conversation = [
    "I'm planning a trip to Japan in April.",
    "I want to see cherry blossoms.",
    "My budget is about 3000 dollars.",
    "I prefer trains over flying domestically.",
    "I'm travelling with my sister.",
]

print("[bold cyan]Message count after each turn:[/bold cyan]")
previous = 0
for text in conversation:
    count = turn(text)
    # Without summarization this would climb 2, 4, 6, 8, 10... Instead it
    # plateaus: old turns keep getting folded into a compact summary.
    marker = " [green]<- compressed[/green]" if count <= previous else ""
    print(f"  after '{text[:34]:34}' -> {count:2} messages{marker}")
    previous = count

# %% Step 4: Look at what survived
# The history now holds a summary standing in for the early turns, plus the
# most recent messages kept verbatim.
state = agent.get_state(CONFIG)
print(f"\n[bold cyan]Final history ({len(state.values['messages'])} messages, "
      f"not {2 * len(conversation)}):[/bold cyan]")
for message in state.values["messages"]:
    kind = message.__class__.__name__.replace("Message", "")
    content = message.content
    if isinstance(content, list):
        content = "".join(b.get("text", "") for b in content if isinstance(b, dict))
    print(f"  [magenta]{kind:6}[/magenta] {str(content).strip()[:88]}")

# %% Step 5: Compression is not amnesia
# The details from the early, summarized turns should still be answerable —
# that is the whole point: fewer tokens, same knowledge.
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Remind me: when am I going, and with whom?"}]},
    config=CONFIG,
)
answer = result["messages"][-1].content
if isinstance(answer, list):
    answer = "".join(b.get("text", "") for b in answer if isinstance(b, dict))
print(f"\n[bold green]Recall after compression:[/bold green] {str(answer).strip()}")

# %% Step 6: The other half of context management
# Besides summarizing conversations, deepagents automatically OFFLOADS huge tool
# results (>20k tokens) to a file in the backend and leaves a short preview plus
# the path behind. The agent can read_file it back on demand — so one giant API
# response can never blow up the whole conversation.
print("\n[dim]Also automatic: tool results over ~20k tokens are written to a[/dim]")
print("[dim]file and replaced with a preview + path the agent can read later.[/dim]")

# %%
