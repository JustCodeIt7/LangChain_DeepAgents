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

from langchain_ollama import ChatOllama

load_dotenv()


# Choose your LLM provider by commenting/uncommenting:
#
# Option 1: Ollama (local)
# Make sure Ollama is running and you have pulled the model (e.g., ollama pull qwen3.5:2b)
model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "qwen3.5:2b"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=0,  # repeatable output: the run you rehearse is the run you record
    reasoning=False,  # skip hidden "thinking" tokens: faster, and no empty answers
)
#
# Option 2: OpenRouter
# from langchain_openrouter import ChatOpenRouter
# model = ChatOpenRouter(model="meta/muse-spark-1.3-contributor", temperature=0)

def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: Why the default backend cannot run commands
# `execute` is only offered to the model when the backend can actually run a
# shell. On the default StateBackend (a virtual filesystem) it is hidden, and a
# call to it anyway just returns an error — a safe default. Let's confirm that.
virtual_agent = create_deep_agent(model=model, backend=StateBackend())
denied = virtual_agent.invoke(
    {"messages": [{"role": "user", "content": "Use the execute tool to run: echo hi"}]}
)

print("[bold cyan]1. StateBackend (virtual, no shell):[/bold cyan]")
print(f"  agent: [dim]{text_of(denied['messages'][-1]).strip()[:110]}...[/dim]")

# %% Step 3: Prepare a scratch workspace
# Notebooks have no __file__; they run from the episode folder.
HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
WORKSPACE = HERE / "workspace"
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
    model=model,
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

