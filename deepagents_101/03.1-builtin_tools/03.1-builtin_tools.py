"""
03.1 - Built-in Tools
=====================
- Every deep agent gets filesystem tools and a `task` subagent tool for free
- `LocalShellBackend` adds `execute`; `TodoListMiddleware` adds `write_todos`
- Demo: four short prompts that make the agent use all ten tools, then a scorecard

Run:  python 03.1-builtin_tools.py
"""

# %% Step 1: Imports and setup
import os
import shutil
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend  # real files + a real shell
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware  # supplies write_todos
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

# %% Step 2: A throwaway workspace the agent is allowed to change
# Rebuilt on every run, so each take of the demo starts from the same files.
# Notebooks have no __file__; they run from the episode folder.
HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
WORKSPACE = HERE / "workspace"
shutil.rmtree(WORKSPACE, ignore_errors=True)
(WORKSPACE / "data").mkdir(parents=True)
(WORKSPACE / "data" / "fruits.txt").write_text("apple\nbanana\ncherry\n")
(WORKSPACE / "data" / "colors.txt").write_text("red\nblue\ngreen\n")
(WORKSPACE / "notes.md").write_text("# Notes\n- status: draft\n")

# %% Step 3: Build an agent that has EVERY built-in tool
# Free with any deep agent:  ls, read_file, write_file, edit_file, delete, glob, grep, task
# Added by the backend:      execute      (LocalShellBackend can run a shell — ep. 07)
# Added by the middleware:   write_todos  (planning is opt-in in 0.7 — ep. 04)
agent = create_deep_agent(
    model=model,
    backend=LocalShellBackend(root_dir=str(WORKSPACE), timeout=30),
    middleware=[TodoListMiddleware()],
    system_prompt=(
        "You are demonstrating your built-in tools. Call each tool the user names, "
        "in the order given, one at a time. Reply with one short sentence."
    ),
)

# %% Step 4: Four prompts, one tool family each
# Naming the tool in the prompt keeps a small model on script. File tools take
# paths from the workspace root (/data/...); the shell runs inside the workspace.
PROMPTS = {
    "Explore": (
        "Use ls on /data. Use read_file on /data/fruits.txt. Use glob with pattern "
        "**/*.txt. Use grep to search for 'blue'."
    ),
    "Change": (
        "Use write_file to create /data/veggies.txt containing carrot and pepper on "
        "separate lines. Then use edit_file on /notes.md to replace 'draft' with 'final'."
    ),
    "Run": (
        "Use execute to run exactly: wc -l data/fruits.txt"
        " Then use the delete tool to remove /data/veggies.txt."
    ),
    "Plan and delegate": (
        "Use write_todos to plan two steps. Then call the task tool so that a subagent "
        "reads /data/colors.txt and lists the colors."
    ),
}

BUILT_INS = ["ls", "read_file", "glob", "grep", "write_file", "edit_file", "execute",
             "delete", "write_todos", "task"]
called = []

for title, prompt in PROMPTS.items():
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    # Every tool call is recorded on the AI messages in the returned state.
    tools = [c["name"] for m in result["messages"] for c in getattr(m, "tool_calls", None) or []]
    called += tools
    print(f"\n[bold magenta]{title}[/bold magenta]  [dim]{prompt}[/dim]")
    print(f"  tools:  [green]{', '.join(tools) or 'none'}[/green]")
    print(f"  answer: {result['messages'][-1].text.strip()[:160]}")

# %% Step 5: The scorecard — which built-in tools actually fired?
print("\n[bold cyan]Built-in tool coverage[/bold cyan]")
for name in BUILT_INS:
    print(f"  {name:11} {'[green]yes[/green]' if name in called else '[red]no[/red]'}")
print(f"\n[bold]{len(set(called) & set(BUILT_INS))}/{len(BUILT_INS)} tools used[/bold]")

# %% Step 6: Proof on disk — the agent's edits are real files
print(f"\n[bold cyan]notes.md after the run:[/bold cyan]\n{(WORKSPACE / 'notes.md').read_text()}")
