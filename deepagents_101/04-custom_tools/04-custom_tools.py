"""
03 - Adding Your Own Tools
==========================
- Two ways to write a tool: a plain function, or the `@tool` decorator
- The docstring IS the tool description the model reads — write it for the model
- Custom tools are ADDITIVE: you keep every built-in tool as well

Run:  python 03-custom_tools.py
"""

# %% Step 1: Imports and setup
import asyncio
import os
from typing import Literal

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.tools import tool
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


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


# %% Step 4: Return structured data for the model to reason over
PRODUCTS = {
    "widget": {"price": 9.99, "in_stock": True},
    "gadget": {"price": 24.50, "in_stock": False},
}


def lookup_product(name: str) -> dict:
    """Look up a product's price and stock status.

    Args:
        name: The product name, such as 'widget' or 'gadget'.
    """
    return {"error": f"Unknown product: {name}"} if name not in PRODUCTS else PRODUCTS[name]


# %% Step 5: Use Literal to give the model a constrained input schema
@tool
def convert_temperature(value: float, scale: Literal["C", "F"]) -> str:
    """Convert a temperature between Celsius (C) and Fahrenheit (F).

    Args:
        value: The temperature to convert.
        scale: The scale of value. It must be C or F.
    """
    if scale == "C":
        return f"{value:g} C is {value * 9 / 5 + 32:g} F"
    return f"{value:g} F is {(value - 32) * 5 / 9:g} C"


# %% Step 6: Async tools let the agent await an I/O-bound operation
@tool
async def estimate_delivery(order_id: str) -> str:
    """Estimate delivery for an order after checking its shipping service.

    Args:
        order_id: The customer order number.
    """
    await asyncio.sleep(0.2)  # Simulates an API request without a real service.
    return f"Order {order_id} is scheduled to arrive in 2 business days."


# %% Step 7: Hand every custom tool to the agent
# `tools=` ADDS to the built-in suite — it never removes ls/read_file/task/etc.
agent = create_deep_agent(
    model=MODEL,
    tools=[
        word_count,
        reverse_text,
        lookup_product,
        convert_temperature,
        estimate_delivery,
    ],
    system_prompt=(
        "You are a utility assistant. Use every named custom and built-in "
        "tool exactly as requested; do not use execute."
    ),
)

# %% Step 8: Each prompt combines a custom-tool pattern with built-in tools.
# `execute` is omitted because the default StateBackend is not a shell backend.
TASK_PROMPTS = [
    (
        "Use write_file to create /demo.txt with exactly 'deep agents are fun', then use "
        "read_file to read it. Use reverse_text and word_count on the read contents."
    ),
    (
        "Use write_file to create /catalog.txt containing 'widget gadget'. Use glob to "
        "find .txt files and grep to find 'gadget' in /catalog.txt. Then use "
        "lookup_product with the exact name 'gadget' and report its price and stock status."
    ),
    (
        "Use write_file to create /temperature.txt containing '68 F'. Read it, use "
        "convert_temperature to convert 68 F to Celsius, then use edit_file (not a "
        "second write_file) to replace exactly '68 F' with '20 C' and read it again."
    ),
    "Use ls to inspect the virtual filesystem root, then use estimate_delivery for order 12345.",
]


# %% Step 9: Inspect which tools the agent actually called
# `.text` is provider-agnostic: it extracts the text from a message whether
# the provider returned a plain string or a list of content blocks.
async def main() -> None:
    for number, task in enumerate(TASK_PROMPTS, start=1):
        result = await agent.ainvoke({"messages": [{"role": "user", "content": task}]})
        print(f"\n[bold cyan]Task {number}:[/bold cyan] {task}")
        for message in result["messages"]:
            for call in getattr(message, "tool_calls", []) or []:
                print(f"  [green]{call['name']}[/green]({call['args']})")
            if message.__class__.__name__ == "ToolMessage":
                print(f"  [yellow]{message.name}[/yellow] -> {message.text}")
        print(f"  [bold green]Final answer:[/bold green] {result['messages'][-1].text}")


if __name__ == "__main__":
    asyncio.run(main())

# %%
