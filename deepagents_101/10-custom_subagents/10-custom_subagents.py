"""
10 - Customizing Subagents
==========================
- Give a subagent its OWN tools and model, different from the orchestrator
- `CompiledSubAgent` lets you plug in any LangGraph runnable as a subagent
- Two very different ways to build the same kind of building block

Run:  python 10-custom_subagents.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.agents import create_agent  # builds a plain (non-deep) agent
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: A tool that ONLY the subagent should have
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature in Celsius to Fahrenheit.

    Args:
        celsius: The temperature in degrees Celsius.
    """
    return celsius * 9 / 5 + 32


# %% Step 3: Declarative subagent with its own tools and model
# `tools` REPLACES the inherited tool set for this subagent (it does not add to
# it), and `model` overrides the orchestrator's model. Here we reuse MODEL, but
# this is where you would drop in a cheaper or larger model for the sub-task.
converter_subagent = {
    "name": "converter",
    "description": "Converts Celsius temperatures to Fahrenheit. Use for any unit conversion.",
    "system_prompt": (
        "You convert temperatures. Always use the celsius_to_fahrenheit tool, "
        "then state the result in one short sentence."
    ),
    "tools": [celsius_to_fahrenheit],
    "model": MODEL,
}

# %% Step 4: A pre-compiled graph as a subagent
# Anything that compiles to a LangGraph runnable can become a subagent. This is
# how you reuse an agent you already built elsewhere, unchanged.
haiku_graph = create_agent(
    model=MODEL,
    system_prompt="You write a single three-line haiku. Output only the haiku.",
)

haiku_subagent = {
    "name": "poet",
    "description": "Writes a three-line haiku about a given topic. Use for any poem request.",
    "runnable": haiku_graph,  # <- CompiledSubAgent: a runnable instead of a prompt
}

# %% Step 5: Wire both into one orchestrator
agent = create_deep_agent(
    model=MODEL,
    subagents=[converter_subagent, haiku_subagent],
    system_prompt=(
        "You are a coordinator. Delegate each sub-task to the right subagent with "
        "the task tool: temperatures to 'converter', poems to 'poet'. "
        "Then report both results in one sentence."
    ),
)

# %% Step 6: One request, two different subagents
task = "Convert 25 degrees Celsius to Fahrenheit, and write a haiku about winter."
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

print("[bold cyan]Delegations:[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        if call["name"] == "task":
            print(f"  -> [green]{call['args'].get('subagent_type')}[/green]")

print("\n[bold cyan]Subagent results:[/bold cyan]")
for message in result["messages"]:
    if message.__class__.__name__ == "ToolMessage" and message.name == "task":
        print(f"[yellow]{text_of(message).strip()}[/yellow]\n")

print(f"[bold green]Final answer:[/bold green] {text_of(result['messages'][-1])}")

# %%
