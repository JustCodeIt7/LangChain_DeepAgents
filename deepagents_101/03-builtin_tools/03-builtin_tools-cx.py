"""
03 - Built-in Tools
===================
Deep Agents supplies filesystem tools and a `task` subagent tool automatically.
`LocalShellBackend` also exposes `execute`; TodoListMiddleware opts into
`write_todos`. This demo makes every tool act in a disposable lesson workspace.

Run: python 03-builtin_tools-cx.py
Override: DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 03-builtin_tools-cx.py
"""

# %% Step 1: Imports and model configuration
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")
WORKSPACE = Path(__file__).parent / "workspace"
BUILT_INS = (
    "write_todos",
    "ls",
    "read_file",
    "write_file",
    "edit_file",
    "glob",
    "grep",
    "execute",
    "task",
    "delete",
)


# %% Step 2: Create safe, repeatable data for the agent to explore
def seed_workspace() -> None:
    """Reset only this tutorial's sample files before each run."""
    data = WORKSPACE / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "fruits.txt").write_text("apple\nbanana\ncherry\n")
    (data / "colors.txt").write_text("red\nblue\ngreen\n")
    (WORKSPACE / "notes.md").write_text("# Notes\n- status: draft\n")
    (data / "veggies.txt").unlink(missing_ok=True)


# %% Step 3: Build an agent with every available harness tool
def build_agent():
    """LocalShellBackend adds execute; middleware adds write_todos."""
    backend = LocalShellBackend(root_dir=str(WORKSPACE.resolve()), timeout=30)
    return create_deep_agent(
        model=MODEL,
        backend=backend,
        middleware=[TodoListMiddleware()],
        system_prompt="""You are demonstrating Deep Agents tools in a throwaway workspace.
For every requested operation, call the named tool exactly; never replace a
filesystem operation with execute. Use relative paths. Keep final answers brief.""",
    )


# %% Step 4: Short prompts that explicitly cover every tool
PROMPTS = [
    "Use write_todos to plan these two items, then use ls on data and "
    "read_file on data/fruits.txt.",
    "Use write_file to create data/veggies.txt containing carrot, pepper, "
    "and basil on separate lines. "
    "Then use edit_file to change 'draft' to 'final' in notes.md.",
    "Use glob to find every .txt file. Use grep to find the file containing 'blue'. "
    "Use execute to run exactly: wc -l data/*.txt",
    "Use task to delegate counting all lines in data/*.txt to a subagent. "
    "Then use delete to remove "
    "data/veggies.txt, complete the todos, and summarize the results.",
]


def tool_names(messages: list) -> set[str]:
    """Collect tool names from the agent's LangChain messages."""
    return {
        call["name"]
        for message in messages
        for call in (getattr(message, "tool_calls", []) or [])
    }


# %% Step 5: Run the guided conversation and report actual coverage
def main() -> None:
    """Invoke each prompt, preserving messages so the agent can continue its plan."""
    seed_workspace()
    agent, messages, called = build_agent(), [], set()
    print(f"[dim]model: {MODEL}  workspace: {WORKSPACE}[/dim]")

    for turn, prompt in enumerate(PROMPTS, start=1):
        print(f"\n[bold magenta]--- Turn {turn} ---[/bold magenta]")
        result = agent.invoke({"messages": messages + [{"role": "user", "content": prompt}]})
        messages = result["messages"]
        new_calls = tool_names(messages) - called
        called.update(new_calls)
        print("tools:", ", ".join(sorted(new_calls)) or "none")

    print("\n[bold cyan]Built-in tool coverage[/bold cyan]")
    for name in BUILT_INS:
        marker = "[green]yes[/green]" if name in called else "[red]no[/red]"
        print(f"  {name:11} {marker}")
    print(f"\n[bold green]Final answer:[/bold green] {messages[-1].text}")


if __name__ == "__main__":
    main()
