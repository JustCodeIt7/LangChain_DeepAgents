"""
09 - Delegating to Subagents
============================
- The `task` tool spawns a subagent that works in an ISOLATED context
- Define one with a `SubAgent` dict: name, description, system_prompt (+ tools)
- The orchestrator only sees the subagent's final answer, not its scratch work

Run:  python 09-subagents_basics.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: Define a subagent
# `description` is what the ORCHESTRATOR reads to decide when to delegate —
# write it like a job posting. `system_prompt` is what the SUBAGENT itself
# reads once it is running.
critic_subagent = {
    "name": "critic",
    "description": (
        "Critiques a piece of writing and returns exactly three bullet points "
        "of concrete feedback. Use for any review or critique request."
    ),
    "system_prompt": (
        "You are a blunt writing critic. Given text, reply with exactly three "
        "bullet points of specific, actionable feedback. Nothing else."
    ),
}

# %% Step 3: Give it to the orchestrator
# Every deep agent also gets a built-in "general-purpose" subagent for free;
# yours are added alongside it.
agent = create_deep_agent(
    model=MODEL,
    subagents=[critic_subagent],
    system_prompt=(
        "You are an editor. When the user asks for a critique, you MUST "
        "delegate it to the 'critic' subagent using the task tool rather than "
        "answering yourself. Then summarize its feedback in one sentence."
    ),
)

# %% Step 4: Run a task worth delegating
draft = "Our product is very good and has many features that users like a lot."
task = f"Please critique this sentence using the critic subagent: '{draft}'"
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

# %% Step 5: See the delegation happen
# One `task` call goes out; one consolidated result comes back. The subagent's
# internal turns never enter the orchestrator's message history — that context
# isolation is the whole point.
print("[bold cyan]Delegation:[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        if call["name"] == "task":
            print(f"  -> subagent [green]{call['args'].get('subagent_type')}[/green]")
            print(f"     brief: [dim]{str(call['args'].get('description'))[:80]}[/dim]")

print("\n[bold cyan]What the subagent returned:[/bold cyan]")
for message in result["messages"]:
    if message.__class__.__name__ == "ToolMessage" and message.name == "task":
        print(f"[yellow]{text_of(message).strip()}[/yellow]")

print(f"\n[bold green]Orchestrator's summary:[/bold green] {text_of(result['messages'][-1])}")

# %%
