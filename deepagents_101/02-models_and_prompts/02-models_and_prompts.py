"""
02 - Models and System Prompts
==============================
- Two ways to specify a model: a "provider:model" string or a model instance
- How `system_prompt` steers the agent (and where it lands in the final prompt)
- `debug=True` for seeing every graph step

Run:  python 02-models_and_prompts.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model  # builds a model from a string spec
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


def ask(agent, question: str) -> str:
    """Invoke an agent with a single question and return its final text."""
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return text_of(result["messages"][-1]).strip()


QUESTION = "In one short sentence, what is LangChain? Do not use tools."

# %% Step 2: Option A — pass a "provider:model" string
# deepagents hands the string to init_chat_model, so any provider LangChain
# supports works: "ollama:...", "openai:...", "anthropic:...", "google_genai:..."
string_agent = create_deep_agent(model=MODEL)
print("[bold cyan]A. model as a string[/bold cyan]")
print(f"  spec: [yellow]{MODEL}[/yellow]")
print(f"  {ask(string_agent, QUESTION)}\n")

# %% Step 3: Option B — pass a pre-built model instance
# Build the model yourself when you need to tune parameters (temperature,
# max_tokens, timeouts, base_url...). deepagents uses the instance as-is.
llm = init_chat_model(MODEL, temperature=0)
instance_agent = create_deep_agent(model=llm)
print("[bold cyan]B. model as an instance[/bold cyan]")
print(f"  class: [yellow]{type(llm).__name__}[/yellow] (temperature=0)")
print(f"  {ask(instance_agent, QUESTION)}\n")

# %% Step 4: The system prompt steers behavior
# IMPORTANT: your `system_prompt` does not REPLACE the deep-agent instructions.
# It is placed FIRST, and the framework's own tool guidance is appended after it.
# That is why the agent still knows how to use write_file, task, etc.
pirate_agent = create_deep_agent(
    model=MODEL,
    system_prompt="You are a pirate. Answer every question in pirate speak, briefly.",
)
print("[bold cyan]C. custom system_prompt[/bold cyan]")
print(f"  {ask(pirate_agent, QUESTION)}\n")

# %% Step 5: debug=True prints every graph step
# Verbose! Use it while developing to see the model/tool nodes as they execute.
# Keep the question tiny — the trace is long.
print("[bold cyan]D. debug=True (expect a verbose LangGraph trace below)[/bold cyan]")
debug_agent = create_deep_agent(model=MODEL, debug=True)
answer = ask(debug_agent, "Say the word 'ready' and nothing else.")
print(f"\n[bold green]Final answer:[/bold green] {answer}")

# %%
