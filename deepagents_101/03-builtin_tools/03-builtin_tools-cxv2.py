"""
03 - Built-in Tools: A Complete Deep Agent Workspace
=====================================================
- One agent uses planning, filesystem, shell, and delegation tools.
- Each prompt targets a distinct tool group; the final check reports coverage.
- LocalShellBackend is real host shell access: this demo is scoped to ./workspace.

Run:  python 03-builtin_tools-cxv2.py
"""

# %% Step 1: Imports and a tightly scoped workspace
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
WORKSPACE.mkdir(exist_ok=True)
print(MODEL, WORKSPACE)
# LocalShellBackend exposes every filesystem tool plus execute. The agent sees
# only this directory, and subprocesses receive no inherited environment secrets.
backend = LocalShellBackend(root_dir=str(WORKSPACE), timeout=30, inherit_env=False)
agent = create_deep_agent(
    model=MODEL,
    backend=backend,
    middleware=[TodoListMiddleware()],  # opt in to the write_todos tool
    system_prompt=(
        "You are a precise tutorial agent. Follow every requested tool sequence exactly. "
        "Only work inside the workspace. For execute, run only the exact safe command "
        "provided by the user. Keep final answers to one sentence."
    ),
)

# %% Step 2: Prompts that exercise the full built-in tool suite
PROMPTS = [
    (
        "Plan, write, list, and read",
        "First use write_todos for: create and verify a note. Then use write_file to "
        "create /notes.md containing exactly 'the brown fox', use ls to list /, and "
        "use read_file to verify /notes.md. Do each step.",
    ),
    (
        "Edit, glob, and grep",
        "Use edit_file to replace 'brown' with 'swift' in /notes.md. Then use glob to "
        "find Markdown files and grep to find 'swift' in /notes.md. Do not skip tools.",
    ),
    (
        "Delegate",
        "Use the built-in task tool to delegate to the general-purpose subagent. Ask it "
        "to read /notes.md and return its exact contents. Do not read the file yourself.",
    ),
    (
        "Execute and delete",
        "Use execute to run exactly: python -c \"from pathlib import Path; "
        "print(Path('notes.md').read_text().upper())\". Then use delete to remove "
        "/notes.md. Do not run any other command.",
    ),
]
EXPECTED = {
    "write_todos", "write_file", "ls", "read_file", "edit_file", "glob", "grep",
    "task", "execute", "delete",
}


# %% Step 3: Run each prompt in a separate LLM turn and inspect its tool calls
def tool_calls(result: dict) -> set[str]:
    return {
        call["name"]
        for message in result["messages"]
        for call in (getattr(message, "tool_calls", []) or [])
    }


used_tools = set()
for number, (title, prompt) in enumerate(PROMPTS, start=1):
    print(f"\n[bold cyan]{number}. {title}[/bold cyan]")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"configurable": {"thread_id": f"builtins-{number}"}},
    )
    calls = tool_calls(result)
    used_tools.update(calls)
    print(f"  tools: [green]{', '.join(sorted(calls))}[/green]")
    print(f"  answer: {result['messages'][-1].content}")

# %% Step 4: Report whether this model followed every tool-specific prompt
missing = EXPECTED - used_tools
status = "all built-in tools exercised" if not missing else f"missing: {', '.join(sorted(missing))}"
print(f"\n[bold cyan]Coverage:[/bold cyan] [yellow]{status}[/yellow]")

# %%
