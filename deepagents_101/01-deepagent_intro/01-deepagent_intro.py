"""
01 - Your First Deep Agent
==========================
- What a "deep agent" is: an agent harness with a filesystem, planning, and subagents
- The one function you need: `create_deep_agent()`
- Demo: ask a trivial question and inspect the message trace

Run:  python 01-deepagent_intro.py
Model override:  DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 01-deepagent_intro.py
"""

# %% Step 1: Imports and setup
################################ Imports and Environment Setup ################################

import os

from deepagents import create_deep_agent  # the single entry point of the framework
from dotenv import load_dotenv  # loads OPENAI_API_KEY / OLLAMA_BASE_URL from .env
from rich import print  # colorized console output

# Pull API keys and model settings out of .env so no secrets live in the script
load_dotenv()

# if you want to use openai, set DEEPAGENTS_MODEL=openai:gpt-4.1-mini in your .env
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")  # fall back to a small local model
print(f"Using model: {MODEL}")


################################ Message Text Helper ################################
# %%


def text_of(message) -> str:
    """Return a message's text.

    Ollama returns `content` as a plain string, while OpenAI's Responses API
    returns a list of content blocks. This helper normalizes both.
    """
    content = message.content

    # Handle the simple provider shape first: content is already plain text
    if isinstance(content, str):
        return content

    # Otherwise flatten the block list, keeping only dict blocks that carry text
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: What comes in the box
################################ Built-in Tool Inventory ################################

# A deep agent is a regular LangChain agent PLUS a built-in tool suite.
# You get all of these without writing a single tool yourself:
BUILT_IN_TOOLS = {
    "ls / read_file / write_file / edit_file": "a filesystem the agent can work in",
    "glob / grep": "find files by name pattern, search inside file contents",
    "delete": "remove a file (new in deepagents 0.7)",
    "execute": "run shell commands (only with a shell-capable backend, see ep. 07)",
    "task": "spawn a subagent to handle work in isolation (see ep. 09)",
    "write_todos": "plan multi-step work (opt-in in 0.7, see ep. 04)",
}

print("[bold cyan]Built-in tools every deep agent gets:[/bold cyan]")

# Print each tool alongside the reason it exists so viewers connect name to purpose
for name, why in BUILT_IN_TOOLS.items():
    print(f"  [green]{name}[/green] — {why}")

# %% Step 3: Create the agent
################################ Create the Deep Agent ################################

# `model` and `system_prompt` are all you need for a working agent.
# Note there is NO `tools=` argument here — the built-ins above come for free.
agent = create_deep_agent(
    model=MODEL,
    system_prompt="You are a concise assistant. Answer in one short sentence.",  # keep demo output tight
)

print(f"\n[bold]Created a deep agent backed by:[/bold] [yellow]{MODEL}[/yellow]")

# %% Step 4: Run it
################################ Invoke the Agent ################################

# Input is a message list, exactly like any LangChain/LangGraph agent.
# We tell it not to use tools so this first demo stays fast and predictable.
question = "What is 7 times 6? Answer directly without using any tools."
result = agent.invoke({"messages": [{"role": "user", "content": question}]})  # run one turn to completion

# %% Step 5: Inspect what happened
################################ Inspect the Resulting State ################################

# `result` is the final graph state. Two keys matter for now:
#   messages -> the full conversation, including any tool calls
#   files    -> the agent's virtual filesystem (empty here; see ep. 05)
print(f"\n[bold cyan]State keys returned:[/bold cyan] {list(result.keys())}")

print("\n[bold cyan]Message trace:[/bold cyan]")

# Walk the conversation to show how the agent reasoned, one message at a time
for message in result["messages"]:
    kind = message.__class__.__name__.replace("Message", "")  # e.g. HumanMessage -> Human
    body = text_of(message).strip() or "[dim](tool call only)[/dim]"  # tool-call messages carry no text
    print(f"  [magenta]{kind:9}[/magenta] {body}")

# The last message is always the agent's final reply to the user
print(f"\n[bold green]Final answer:[/bold green] {text_of(result['messages'][-1])}")

# %%
