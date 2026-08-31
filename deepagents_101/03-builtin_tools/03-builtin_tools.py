"""
03 - Built-in Tools
==========================
- Every deep agent ships with a built-in tool suite — you write no tool code
- Filesystem tools: ls, read_file, write_file, edit_file, delete, glob, grep
- `execute` is only offered with a shell-capable backend (LocalShellBackend)
- `task` spawns a subagent (on by default); `write_todos` is opt-in middleware
- Demo: four short prompts that together exercise EVERY built-in tool, then a
  coverage check (small local models follow short, scoped prompts much better
  than one giant step list)

Run:  python 03-builtin_tools.py
Model override:  DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 03-builtin_tools.py
"""

# %% Step 1: Imports and setup
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend  # shell-capable -> unlocks `execute`
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware  # opt-in `write_todos`
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


# %% Step 2: Seed a scratch workspace with real files
# LocalShellBackend works on the REAL disk under root_dir, so we create a few
# files for the agent to list, read, search, edit, and delete.
WORKSPACE = Path(__file__).parent / "workspace"
(WORKSPACE / "data").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "data" / "fruits.txt").write_text("apple\nbanana\ncherry\n")
(WORKSPACE / "data" / "colors.txt").write_text("red\nblue\ngreen\n")
(WORKSPACE / "notes.md").write_text("# Notes\n- status: draft\n")

# %% Step 3: Build the agent
# LocalShellBackend -> the `execute` tool is offered (it runs real commands).
# TodoListMiddleware -> adds the `write_todos` planning tool.
# `task` (subagent) comes for free via the default general-purpose subagent.
agent = create_deep_agent(
    model=MODEL,
    backend=LocalShellBackend(root_dir=str(WORKSPACE), timeout=30, inherit_env=False),
    middleware=[TodoListMiddleware()],
    system_prompt=(
        "You are a file-management assistant working in a workspace that contains "
        "data/fruits.txt, data/colors.txt, and notes.md. For each numbered step the "
        "user gives, call the EXACTLY named tool — never substitute the execute/shell "
        "tool for a filesystem step. Use relative paths from the workspace root. "
        "Keep the final summary to one paragraph."
    ),
)

# %% Step 4: Four prompts that together exercise every built-in tool
# All paths are relative to the workspace root: the filesystem tools normalize
# them under the backend root, and the `execute` shell runs with cwd = root.
# We keep the conversation going by appending each result's messages to the
# next invoke — the workspace files persist on disk either way.
PROMPTS = [
    (
        "Plan this work with write_todos (one todo per item), then do each item: "
        "1) Use ls to list the files in the data folder. "
        "2) Use read_file to read data/fruits.txt."
    ),
    (
        "Continue your todo list. 3) Use write_file to create data/veggies.txt with: "
        "carrot, pepper, basil (one per line). "
        "4) Use edit_file to replace the word 'draft' with 'final' in notes.md."
    ),
    (
        "Continue your todo list. 5) Use glob to find every .txt file. "
        "6) Use grep to find which file contains the word 'blue'. "
        "7) Use execute to run exactly: wc -l data/*.txt"
    ),
    (
        "Continue your todo list. 8) Use task to spawn a subagent that counts the "
        "total lines across all .txt files in data. "
        "9) Use delete to delete data/veggies.txt. "
        "Then finish your todo list and give a one-paragraph summary."
    ),
]

messages: list = []
for number, prompt in enumerate(PROMPTS, start=1):
    print(f"\n[bold magenta]--- Turn {number} ---[/bold magenta]")
    result = agent.invoke({"messages": messages + [{"role": "user", "content": prompt}]})

    # Show the tool calls this turn made, named tool first
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []) or []:
            print(f"  [green]{call['name']}[/green]({call['args']})")

    # Carry the full conversation into the next turn so context survives
    messages = result["messages"]

# %% Step 5: Coverage check — which built-in tools actually fired?
BUILT_IN = ["write_todos", "ls", "read_file", "write_file", "edit_file",
            "glob", "grep", "execute", "task", "delete"]
called = {
    call["name"]
    for message in result["messages"]
    for call in (getattr(message, "tool_calls", []) or [])
}
print(f"\n[bold cyan]Built-in tool coverage ({len(called)}/{len(BUILT_IN)}):[/bold cyan]")
for name in BUILT_IN:
    mark = "[green]✓[/green]" if name in called else "[red]✗[/red]"
    print(f"  {mark} [yellow]{name}[/yellow]")

# %% Step 6: Final answer
print(f"\n[bold green]Final answer:[/bold green] {result['messages'][-1].text}")

# %%
