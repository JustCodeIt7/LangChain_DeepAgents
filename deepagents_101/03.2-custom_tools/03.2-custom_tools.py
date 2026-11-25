"""
03.2 - Adding Your Own Tools
============================
- Two ways to write a tool: a plain function, or the `@tool` decorator
- The docstring IS the tool description the model reads — write it for the model
- Custom tools are ADDITIVE: you keep every built-in tool as well

Run:  python 03.2-custom_tools.py
Next: 03.2-custom_tools-v2.py adds async tools and return_direct (extended cut)
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.tools import tool
from rich import print

from langchain_ollama import ChatOllama

################################ Environment & Model Setup ################################

# Load environment variables from a local .env file
load_dotenv()


# Choose your LLM provider by commenting/uncommenting:
#
# Option 1: Ollama (local)
# Make sure Ollama is running and you have pulled the model (e.g., ollama pull qwen3.5:2b)
# Initialize the local chat model with deterministic settings for demos
model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "qwen3.5:2b"),  # Default to a lightweight local model
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),  # Target the local Ollama server
    temperature=0,  # repeatable output: the run you rehearse is the run you record
    reasoning=False,  # skip hidden "thinking" tokens: faster, and no empty answers
)
#
# Option 2: OpenRouter
# from langchain_openrouter import ChatOpenRouter
# model = ChatOpenRouter(model="meta/muse-spark-1.3-contributor", temperature=0)

# %% Step 2: A tool can be a plain Python function
################################ Plain Function Tool ################################


# deepagents inspects the signature and docstring to build the tool schema.
# Keep parameter types simple (str/int/bool) — smaller models coerce them better.
def word_count(text: str) -> int:
    """Count how many words are in the given text.

    Args:
        text: The text whose words should be counted.
    """
    return len(text.split())  # Split on whitespace to count words


# %% Step 3: ...or use the @tool decorator
################################ Decorated Tool ################################


# Same result, but the decorator gives you explicit control (custom name,
# args schema, return_direct, etc.) and turns it into a real BaseTool object.
@tool
def reverse_text(text: str) -> str:
    """Reverse the characters of the given text.

    Args:
        text: The text to reverse.
    """
    return text[::-1]  # Slice with a negative step to reverse the string


# %% Step 4: A tool can return STRUCTURED data (a dict), not just a string
################################ Structured Data Tool ################################

# The dict is serialized to JSON, so the model can read individual fields.
# Define a mock product catalog for the lookup tool
PRODUCTS = {
    "widget": {"price": 9.99, "in_stock": True},
    "gadget": {"price": 24.50, "in_stock": False},
}


def lookup_product(name: str) -> dict:
    """Look up a product's price and stock status.

    Args:
        name: The product name, such as 'widget' or 'gadget'.
    """
    # Normalize the product name to lowercase and return an error dict if missing
    return PRODUCTS.get(name.lower(), {"error": f"Unknown product: {name}"})


# %% Step 5: Hand the tools to the agent
################################ Agent & Output Helper ################################

# `tools=` ADDS to the built-in suite — it never removes ls/read_file/task/etc.
# Build the agent by combining the LLM, custom tools, and behavioral instructions
agent = create_deep_agent(
    model=model,
    tools=[word_count, reverse_text, lookup_product],  # Register custom tools alongside built-in ones
    system_prompt="You are a utility assistant. Use the tools the user names. Be brief.",
)


def show(title: str, task: str) -> None:
    """Run one task, then print each tool call, its result, and the final answer."""
    # Send the user task to the agent and capture the full message trace
    result = agent.invoke({"messages": [{"role": "user", "content": task}]})
    print(f"\n[bold cyan]{title}[/bold cyan]  [dim]{task}[/dim]")
    # Iterate through the conversation history to display tool calls and their outputs
    for message in result["messages"]:
        # AI messages carry the tool CALLS; ToolMessages carry the RESULTS.
        # Safely extract and print any tool calls attached to the current message
        for call in getattr(message, "tool_calls", None) or []:
            print(f"  [green]{call['name']}[/green]({call['args']})")
        # Print the returned payload when the message is a tool execution result
        if message.__class__.__name__ == "ToolMessage":
            print(f"  [yellow]{message.name}[/yellow] -> {message.text}")
    # `.text` is provider-agnostic: a plain string or a list of content blocks.
    print(f"  [bold green]Final answer:[/bold green] {result['messages'][-1].text.strip()}")


# %% Step 6: One request, two custom tools
################################ Example Runs ################################

# Chain two custom tools together in a single prompt
show("1. Two tools", "Use reverse_text on 'deep agents are fun', then use word_count on it.")

# %% Step 7: The model reads fields out of the dict
# Query structured dictionary data and let the model extract specific fields
show("2. Structured data", "Use lookup_product for 'gadget'. What does it cost, and is it in stock?")

# %% Step 8: Proof that custom tools are additive — a built-in and a custom tool together
# Combine a built-in filesystem tool with a custom tool in the same request
show(
    "3. Built-in + custom",
    "Use write_file to save 'hello tools' to /demo.txt, then use word_count on 'hello tools'.",
)

# %%