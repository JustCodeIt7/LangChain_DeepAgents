"""
03 - Built-in Tools: A Complete Deep Agent Workspace
=====================================================
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
from langchain_ollama import ChatOllama
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:0.8b")
MODEL = "openai:gpt-4.1-mini"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
model = ChatOllama(
    model=MODEL.removeprefix("ollama:"), base_url=OLLAMA_BASE_URL
)
WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)
print(MODEL, OLLAMA_BASE_URL)
# LocalShellBackend exposes every filesystem tool plus execute. The agent sees
# only this directory, and subprocesses receive no inherited environment secrets.
backend = LocalShellBackend(root_dir=str(WORKSPACE), timeout=30, inherit_env=False)
agent = create_deep_agent(
    model=model,
    backend=backend,
    middleware=[TodoListMiddleware()],  # opt in to the write_todos tool
    subagents=[
        {
            "name": "reporter",
            "description": "Returns a fixed confirmation for delegation demos.",
            "system_prompt": "Reply exactly: delegated task complete.",
        }
    ],
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
        "Use the built-in task tool to delegate to the reporter subagent. Ask it to "
        "reply with its fixed confirmation. Do no other work.",
    ),
    (
        "Execute and delete",
        'Use execute to run exactly: python -c "from pathlib import Path; '
        "print(Path('notes.md').read_text().upper())\". Then use delete to remove "
        "/notes.md. Do not run any other command.",
    ),
]
EXPECTED = {
    "write_todos", "write_file", "ls", "read_file", "edit_file", "glob", "grep",
    "task", "execute", "delete",
}
used_tools = set()
for number, (title, prompt) in enumerate(PROMPTS, start=1):
    print(f"\n[bold cyan]{number}. {title}[/bold cyan]")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"recursion_limit": 12, "configurable": {"thread_id": f"builtins-{number}"}},
        )
    except Exception as error:
        print(f"  [red]Prompt failed: {error}[/red]")
        continue
    calls = {
        call["name"] for message in result["messages"]
        for call in (getattr(message, "tool_calls", []) or [])
    }
    used_tools.update(calls)
    print(f"  tools: [green]{', '.join(sorted(calls))}[/green]")
    print(f"  answer: {result['messages'][-1].content}")

# %% Step 4: Report whether this model followed every tool-specific prompt
missing = EXPECTED - used_tools
status = "all built-in tools exercised" if not missing else f"missing: {', '.join(sorted(missing))}"
print(f"\n[bold cyan]Coverage:[/bold cyan] [yellow]{status}[/yellow]")
# %%
