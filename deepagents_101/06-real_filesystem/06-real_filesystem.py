"""
06 - Working on Real Files (FilesystemBackend)
==============================================
- Swap the virtual backend for `FilesystemBackend` to edit real files on disk
- `root_dir` scopes the agent; `virtual_mode=True` blocks escapes like ../
- Agent paths are relative to root_dir — "/notes.md" means "<root_dir>/notes.md"

Run:  python 06-real_filesystem.py
"""

# %% Step 1: Imports and setup
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend  # reads/writes actual files
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


# %% Step 2: Prepare a scratch workspace next to this script
# Always scope a real filesystem agent to a directory you are happy for it to
# modify. Here we use ./workspace inside the episode folder.
WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)
(WORKSPACE / "shopping.md").write_text("# Shopping\n- milk\n")

print(f"[bold cyan]Workspace:[/bold cyan] [yellow]{WORKSPACE}[/yellow]")
print(f"  seeded: {[p.name for p in WORKSPACE.iterdir()]}")

# %% Step 3: Point the backend at that directory
# virtual_mode=True (the default) sandboxes paths inside root_dir, so the agent
# cannot wander into ../ or ~/ even if it tries.
backend = FilesystemBackend(root_dir=str(WORKSPACE), virtual_mode=True)

agent = create_deep_agent(
    model=MODEL,
    backend=backend,
    system_prompt=(
        "You are a file assistant working in the user's workspace. "
        "Paths are relative to the workspace root, e.g. /shopping.md. "
        "Keep replies to one sentence."
    ),
)

# %% Step 4: Ask it to touch real files
# Note the path style: "/shopping.md", NOT "workspace/shopping.md" — root_dir
# already scopes it. Using the folder name again would create workspace/workspace/.
task = (
    "Add the line '- eggs' to /shopping.md, then create /greeting.txt "
    "containing exactly: Hello from deepagents"
)
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

print(f"\n[bold green]Agent says:[/bold green] {text_of(result['messages'][-1])}")

# %% Step 5: Prove it — read the files with plain Python, no agent involved
# This is the payoff of a real backend: the changes outlive the run.
print("\n[bold cyan]Files on disk after the run:[/bold cyan]")
for path in sorted(WORKSPACE.iterdir()):
    print(f"\n[yellow]{path.name}[/yellow]")
    print(path.read_text())

# %%
