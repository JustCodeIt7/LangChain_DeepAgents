"""
07 - Running Shell Commands (LocalShellBackend)
===============================================
- The `execute` tool is only offered when the backend can run a shell
- `LocalShellBackend` = FilesystemBackend + real subprocess execution
- SAFETY: this runs real commands on your machine. There is NO sandbox.

Run:  python 07-shell_execute.py
"""

# %% Step 1: Imports and setup
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend, StateBackend
from dotenv import load_dotenv
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:9b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: Why the default backend cannot run commands
# The `execute` tool is only attached when the backend can actually run a
# shell. On the default StateBackend (a virtual filesystem) the tool is not
# offered to the model at all — a safe default. Let's confirm that.
virtual_agent = create_deep_agent(model=MODEL, backend=StateBackend())
denied = virtual_agent.invoke(
    {"messages": [{"role": "user", "content": "Use the execute tool to run: echo hi"}]}
)
attempted = [
    call
    for message in denied["messages"]
    for call in (getattr(message, "tool_calls", []) or [])
    if call["name"] == "execute"
]

print("[bold cyan]1. StateBackend (virtual, no shell):[/bold cyan]")
print(f"  execute tool calls: [red]{len(attempted)}[/red]")
print(f"  agent: [dim]{text_of(denied['messages'][-1]).strip()[:100]}...[/dim]")

# %% Step 3: Prepare a scratch workspace
WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)

# %% Step 4: Build a shell-capable backend
# timeout caps how long a single command may run.
# env / inherit_env control which environment variables the command sees;
# inherit_env=False (the default) keeps your secrets out of the subprocess.
shell_backend = LocalShellBackend(
    root_dir=str(WORKSPACE),
    timeout=30,
    inherit_env=False,
)

agent = create_deep_agent(
    model=MODEL,
    backend=shell_backend,
    system_prompt=(
        "You are a shell assistant. Use the execute tool to run the exact "
        "command the user asks for. Keep replies to one sentence."
    ),
)

# %% Step 5: Run one explicit, safe command
# Be specific about the command. Never let untrusted input reach this agent —
# whatever it decides to run WILL run with your user's permissions.
task = "Run this shell command exactly: echo 'hello from the shell' > greeting.txt"
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

print("\n[bold cyan]2. LocalShellBackend — commands executed:[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        if call["name"] == "execute":
            print(f"  [green]$ {call['args'].get('command')}[/green]")

print(f"\n[bold green]Agent says:[/bold green] {text_of(result['messages'][-1])}")

# %% Step 6: Verify the side effect on real disk
created = WORKSPACE / "greeting.txt"
print("\n[bold cyan]greeting.txt on disk:[/bold cyan]")
print(f"[yellow]{created.read_text() if created.exists() else '(not created)'}[/yellow]")

# %%
