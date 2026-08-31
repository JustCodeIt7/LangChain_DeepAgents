"""
03 - Built-in Tools
==========================
- Every deep agent ships with a built-in tool suite — you write no tool code
- Filesystem tools: ls, read_file, write_file, edit_file, delete, glob, grep
- `execute` is only offered with a shell-capable backend (LocalShellBackend)
- `task` spawns a subagent (on by default); `write_todos` is opt-in middleware
- Demo: ONE prompt that exercises every built-in tool, then a coverage check

Run:  python 03-builtin_tools.py
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

# %% Step 4: One prompt that exercises every built-in tool
# All paths are relative to the workspace root: the filesystem tools normalize
# them under the backend root, and the `execute` shell runs with cwd = root.
task = (
    "Work in your workspace. Complete these steps IN ORDER, using the named tool for each:\n"
    "1. write_todos — plan the steps below as todos.\n"
    "2. ls — list the files in the data folder.\n"
    "3. read_file — read data/fruits.txt.\n"
    "4. write_file — create data/veggies.txt with: carrot, pepper, basil (one per line).\n"
    "5. edit_file — in notes.md replace the word 'draft' with 'final'.\n"
    "6. glob — find every .txt file.\n"
    "7. grep — search all files for the word 'blue'.\n"
    "8. execute — run this shell command exactly: wc -l data/*.txt\n"
    "9. task — spawn a subagent to count the total lines across all .txt files in data.\n"
    "10. delete — delete data/veggies.txt.\n"
    "Finish with a one-paragraph summary of what you did."
)
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

# %% Step 5: Coverage check — which built-in tools actually fired?
BUILT_IN = ["write_todos", "ls", "read_file", "write_file", "edit_file",
            "glob", "grep", "execute", "task", "delete"]
called = {
    call["name"]
    for message in result["messages"]
    for call in (getattr(message, "tool_calls", []) or [])
}
print("[bold cyan]Built-in tool coverage:[/bold cyan]")
for name in BUILT_IN:
    mark = "[green]✓[/green]" if name in called else "[red]✗[/red]"
    print(f"  {mark} [yellow]{name}[/yellow]")

# %% Step 6: Full tool-call trace
print("\n[bold cyan]Tool calls made:[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        print(f"  [green]{call['name']}[/green]({call['args']})")

print(f"\n[bold green]Final answer:[/bold green] {result['messages'][-1].text}")

# %%
