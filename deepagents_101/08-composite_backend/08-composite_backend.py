"""
08 - Mixing Backends (CompositeBackend)
=======================================
- Route different paths to different backends in ONE agent
- `default=` handles everything; `routes=` overrides by path prefix
- Longest matching prefix wins

Run:  python 08-composite_backend.py
"""

# %% Step 1: Imports and setup
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
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


# %% Step 2: Prepare the real directory that /disk/ will map to
WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)
for stale in WORKSPACE.iterdir():
    stale.unlink()

# %% Step 3: Build the composite backend
# Think of `routes` as mount points:
#   /disk/...  -> real files under ./workspace   (survives the run)
#   everything else -> virtual state files        (discarded after the run)
backend = CompositeBackend(
    default=StateBackend(),
    routes={"/disk/": FilesystemBackend(root_dir=str(WORKSPACE), virtual_mode=True)},
)

print("[bold cyan]Mount table:[/bold cyan]")
print("  [yellow]/disk/[/yellow]     -> FilesystemBackend (real ./workspace)")
print("  [yellow]everything else[/yellow] -> StateBackend (virtual, in-memory)")

agent = create_deep_agent(
    model=MODEL,
    backend=backend,
    system_prompt=(
        "You are a file assistant. Follow the user's numbered steps exactly, "
        "using write_file and read_file. Keep replies to one sentence."
    ),
)

# %% Step 4: Move data across the boundary
# The agent writes to the virtual side, reads it back, and copies it to the
# real side. It uses the same tools for both — only the path prefix differs.
task = (
    "Do these steps in order: "
    "1) write_file to /scratch/note.md with the content 'ideas for episode 8', "
    "2) read_file /scratch/note.md, "
    "3) write_file that same content to /disk/note.md."
)
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

print("\n[bold cyan]Tool calls (watch the path prefixes):[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        path = call["args"].get("file_path", "")
        print(f"  [green]{call['name']}[/green] [yellow]{path}[/yellow]")

print(f"\n[bold green]Agent says:[/bold green] {text_of(result['messages'][-1])}")

# %% Step 5: Prove each half landed in a different place
# The virtual file is only in the returned state...
print("\n[bold cyan]Virtual side — result['files'] keys:[/bold cyan]")
print(f"  {list(result['files'].keys())}")

# ...while the /disk/ file is a genuine file you can open with plain Python.
disk_file = WORKSPACE / "note.md"
on_disk = disk_file.read_text() if disk_file.exists() else "(missing)"
print("\n[bold cyan]Real side — ./workspace on disk:[/bold cyan]")
print(f"  {disk_file.name}: [yellow]{on_disk}[/yellow]")

# %%
