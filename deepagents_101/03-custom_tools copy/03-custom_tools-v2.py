"""
03 - Adding Your Own Tools
==========================
- Two ways to write a tool: a plain function, or the `@tool` decorator
- The docstring IS the tool description the model reads — write it for the model
- Custom tools are ADDITIVE: you keep every built-in tool as well
- Tools can return STRUCTURED data (dicts), be ASYNC, or SHORT-CIRCUIT
  with return_direct=True

Run:  python 03-custom_tools.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_core.tools import tool  # decorator form for tools
from rich import print
import asyncio

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
# `.text` is provider-agnostic: it extracts the text from a message whether
# the provider returned a plain string or a list of content blocks.
print("[bold cyan]Tool calls made:[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        print(f"  [green]{call['name']}[/green]({call['args']})")

print("\n[bold cyan]Tool results:[/bold cyan]")
for message in result["messages"]:
    if message.__class__.__name__ == "ToolMessage":
        print(f"  [yellow]{message.name}[/yellow] -> {message.text}")

print(f"\n[bold green]Final answer:[/bold green] {result['messages'][-1].text}")

# %% Step 7: A tool can return STRUCTURED data (a dict), not just a string
# The dict is serialized to JSON and handed to the model, which can read
# specific fields and reason over them. Great for "lookup" style tools.
PRODUCTS = {
    "widget": {"price": 9.99, "in_stock": True, "category": "tools"},
    "gadget": {"price": 24.50, "in_stock": False, "category": "electronics"},
    "doohickey": {"price": 3.75, "in_stock": True, "category": "tools"},
}


def lookup_product(name: str) -> dict:
    """Look up a product in the catalog and return its details.

    Args:
        name: The product name to look up (e.g. 'widget').
    """
    product = PRODUCTS.get(name)
    if product is None:
        return {"error": f"Unknown product: {name}"}
    return {"name": name, **product}


# %% Step 8: A tool can be ASYNC
# Use `async def` for I/O-bound work (API calls, DB queries). The model calls
# it just like a sync tool — but the agent must run on the async path
# (.ainvoke), since an async-only tool can't be called synchronously.

QUOTES = {"AAPL": 213.40, "MSFT": 415.10, "NVDA": 132.80}


@tool
async def fetch_quote(symbol: str) -> str:
    """Fetch the current stock price for a ticker symbol.

    Args:
        symbol: The stock ticker symbol (e.g. 'AAPL').
    """
    await asyncio.sleep(0.5)  # simulate a network round-trip
    price = QUOTES.get(symbol.upper())
    if price is None:
        return f"No quote found for {symbol}"
    return f"{symbol.upper()} is trading at ${price:.2f}"


# %% Step 9: A tool can SHORT-CIRCUIT with return_direct=True
# Normally the model reads the tool result and writes its own answer. With
# return_direct=True, the tool's output IS the final answer — no extra LLM call.
# Use it when the tool already produces the exact text you want to show the user.
@tool(return_direct=True)
def get_order_status(order_id: str) -> str:
    """Get the current status of a customer order.

    Args:
        order_id: The order number (e.g. '12345').
    """
    return f"Order #{order_id} is shipped and will arrive in 2 days."


# %% Step 10: Build an agent with the three new tools
agent2 = create_deep_agent(
    model=MODEL,
    tools=[lookup_product, fetch_quote, get_order_status],
    system_prompt=(
        "You are a helpful assistant with access to a product catalog, a stock "
        "quote service, and an order status service. Use the right tool for each "
        "request. Do not use any filesystem tools."
    ),
)


def show_tool_calls(result, label):
    """Print the tool calls, tool results, and final answer for one run."""
    print(f"\n[bold cyan]{label}[/bold cyan]")
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []) or []:
            print(f"  [green]{call['name']}[/green]({call['args']})")
    for message in result["messages"]:
        if message.__class__.__name__ == "ToolMessage":
            print(f"  [yellow]{message.name}[/yellow] -> {message.text}")
    print(f"  [bold green]Final answer:[/bold green] {result['messages'][-1].text}")


# One event loop, shared by every run_task call. The Ollama async client keeps
# a connection pool bound to a single loop, so we reuse one loop instead of
# calling asyncio.run() per task (which closes the loop between tasks).
_AGENT_LOOP = None


def run_task(agent, task):
    """Run one task on the agent via the async path, reusing one event loop.

    agent2 has an async tool (fetch_quote), so we must use ainvoke — a
    StructuredTool built from `async def` raises on sync .invoke().
    """
    global _AGENT_LOOP
    if _AGENT_LOOP is None or _AGENT_LOOP.is_closed():
        _AGENT_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_AGENT_LOOP)
    return _AGENT_LOOP.run_until_complete(agent.ainvoke({"messages": [{"role": "user", "content": task}]}))


# %% Step 11: Task 1 — structured return
# The model calls lookup_product, gets a dict back, and reads the fields.
# Try also: "How much is the doohickey, and is it in stock?"
#           "Look up the product 'sprocket'."  (unknown -> error path)
result1 = run_task(agent2, "Look up the product 'gadget' and tell me its price and whether it's in stock.")
show_tool_calls(result1, "Task 1 — structured return (lookup_product)")


# %% Step 12: Task 2 — async tool
# The model calls fetch_quote (an async tool); the framework awaits it.
# Try also: "What's the price of NVDA?"
#           "What are the prices of AAPL and MSFT?"  (two calls)
result2 = run_task(agent2, "What is the current stock price of MSFT?")
show_tool_calls(result2, "Task 2 — async tool (fetch_quote)")


# %% Step 13: Task 3 — return_direct
# The model calls get_order_status; because return_direct=True, the tool's
# output is returned as the final answer with NO extra LLM call.
# Try also: "Check the status of order #777."
#           "Is order #42 delivered yet?"
result3 = run_task(agent2, "What is the status of order #12345?")
show_tool_calls(result3, "Task 3 — return_direct (get_order_status)")

# %%
