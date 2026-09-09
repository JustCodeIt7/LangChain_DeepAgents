"""
DeepCoder 01 - Your First Coding Agent
======================================
- `create_deep_agent()` gives you a working agent in one call
- The model is a plain string: "ollama:qwen3.5:9b" runs entirely on your machine
- Every answer comes back as a list of messages; the last one is the reply

Run:  python main.py
Ask:  python main.py "explain what a deep agent is"
"""

# %% Step 1: Imports and setup
import os
import sys

from deepagents import create_deep_agent
from dotenv import load_dotenv
from rich import print
from rich.markdown import Markdown

# Reads the repo-root .env so you can keep model settings out of the code.
load_dotenv()

# One env var controls the whole series. Override it to use any LangChain
# provider: "openai:gpt-5.5", "anthropic:claude-sonnet-4-6", "ollama:qwen3.5:4b".
MODEL = os.getenv("DEEPCODER_MODEL", "ollama:qwen3.5:9b")


# %% Step 2: Normalize message content
def text_of(message) -> str:
    """Return a message's text, whether the provider sends a string or blocks.

    Ollama gives you a plain string. OpenAI's newer APIs give you a list of
    content blocks. This helper means the rest of the app never has to care.
    """
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 3: Build the agent
# This is the entire agent. `create_deep_agent` wires up a LangGraph state
# machine with a built-in toolbox already attached:
#
#   ls, read_file, write_file, edit_file, delete, glob, grep  -> a filesystem
#   task                                                      -> delegate to a subagent
#
# Right now those tools operate on a virtual, in-memory filesystem that
# disappears when the process exits. Part 3 points them at real project files.
SYSTEM_PROMPT = """You are DeepCoder, a terminal coding assistant.
Answer concisely. Prefer short code examples over long prose.
When you are unsure about a file's contents, read it rather than guessing."""

agent = create_deep_agent(
    model=MODEL,
    system_prompt=SYSTEM_PROMPT,
)


# %% Step 4: Ask one question and print the answer
def main() -> None:
    """Send a single question to the agent and render the reply."""
    # Use the command-line argument if given, otherwise a default question.
    question = " ".join(sys.argv[1:]) or "In two sentences, what is a coding agent?"

    print(f"[dim]model:[/dim] [cyan]{MODEL}[/cyan]")
    print(f"[bold green]you >[/bold green] {question}\n")

    # .invoke() runs the agent to completion and returns the final state.
    # The state is a dict; "messages" holds the full conversation so far.
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    answer = text_of(result["messages"][-1]).strip()
    print("[bold cyan]deepcoder >[/bold cyan]")
    print(Markdown(answer))


if __name__ == "__main__":
    main()
