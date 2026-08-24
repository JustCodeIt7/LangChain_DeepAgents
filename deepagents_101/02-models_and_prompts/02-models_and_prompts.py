"""
02 - Models and System Prompts
==============================
- Two ways to specify a model: a "provider:model" string or a model instance
- How `system_prompt` steers the agent (and where it lands in the final prompt)
- `debug=True` for seeing every graph step

Run:  python 02-models_and_prompts.py
"""

# %% Step 1: Imports and setup
################################ Imports & Environment ################################

import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model  # builds a model from a string spec
from rich import print

# Pull provider credentials / model overrides from a local .env file
load_dotenv()

# Allow the model to be swapped without editing code; fall back to a small local model
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")

# %%
################################ Helper: Ask an Agent ################################

def ask(agent, question: str) -> str:
    """Invoke an agent with a single question and return its final text."""
    # Messages use the standard chat format so any provider can consume them
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    # `.text` normalizes content across providers (str vs content blocks)
    return result["messages"][-1].text.strip()


# Reuse one question everywhere so differences come from config, not the prompt
QUESTION = "In one short sentence, what is LangChain? Do not use tools."

# %% Step 2: Option A — pass a "provider:model" string
################################ A. Model as a String ################################

# deepagents hands the string to init_chat_model, so any provider LangChain
# supports works: "ollama:...", "openai:...", "anthropic:...", "google_genai:..."
string_agent = create_deep_agent(model=MODEL, temperature=0.1)
print("[bold cyan]A. model as a string[/bold cyan]")
print(f"spec: [yellow]{MODEL}[/yellow]")
print(f"{ask(string_agent, QUESTION)}\n")

# %% Step 3: Option B — pass a pre-built model instance
################################ B. Model as an Instance ################################

# Build the model yourself when you need to tune parameters (temperature,
# max_tokens, timeouts, base_url...). deepagents uses the instance as-is.
llm = init_chat_model(MODEL, temperature=0)  # temperature=0 for deterministic output
instance_agent = create_deep_agent(model=llm)
print("[bold cyan]B. model as an instance[/bold cyan]")
print(f"  class: [yellow]{type(llm).__name__}[/yellow] (temperature=0)")
print(f"  {ask(instance_agent, QUESTION)}\n")

# %% Step 4: The system prompt steers behavior
################################ C. Custom System Prompt ################################

# IMPORTANT: your `system_prompt` does not REPLACE the deep-agent instructions.
# It is placed FIRST, and the framework's own tool guidance is appended after it.
# That is why the agent still knows how to use write_file, task, etc.
pirate_agent = create_deep_agent(
    model=MODEL,
    system_prompt="You are a pirate. Answer every question in pirate speak, briefly.",  # Persona layered on top of built-in instructions
)
print("[bold cyan]C. custom system_prompt[/bold cyan]")
print(f"  {ask(pirate_agent, QUESTION)}\n")

# %% Step 5: debug=True prints every graph step
################################ D. Debugging the Graph ################################

# Verbose! Use it while developing to see the model/tool nodes as they execute.
# Keep the question tiny — the trace is long.
print("[bold cyan]D. debug=True (expect a verbose LangGraph trace below)[/bold cyan]")
debug_agent = create_deep_agent(model=MODEL, debug=True)  # Stream every LangGraph node to stdout
answer = ask(debug_agent, "Say the word 'ready' and nothing else.")  # Minimal prompt keeps the trace readable
print(f"\n[bold green]Final answer:[/bold green] {answer}")

# %%
