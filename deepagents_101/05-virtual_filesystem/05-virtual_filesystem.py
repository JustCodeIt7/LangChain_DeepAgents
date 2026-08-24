"""
05 - The Virtual Filesystem (StateBackend)
==========================================
- Every deep agent has a filesystem; by default it is VIRTUAL (lives in graph state)
- Seed files into the run with `create_file_data` under the `files` key
- Nothing touches your real disk — perfect for safe experimentation

Run:  python 05-virtual_filesystem.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from deepagents.backends import StateBackend  # the default backend, shown explicitly
from deepagents.backends.utils import create_file_data  # builds a seed file entry
from dotenv import load_dotenv
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: Seed the virtual filesystem
# `files` is a dict of path -> FileData. create_file_data() builds the entry
# (content plus timestamps/encoding metadata) so you don't hand-roll the shape.
seed_files = {
    "/notes/todo.md": create_file_data(
        "# Todo\n- [ ] buy milk\n- [ ] write tutorial\n"
    ),
    "/notes/ideas.md": create_file_data("# Ideas\n- a deep agents course\n"),
}

print("[bold cyan]Seeded virtual files:[/bold cyan]")
for path in seed_files:
    print(f"  [yellow]{path}[/yellow]")

# %% Step 3: Build the agent
# StateBackend() is the default — passing it explicitly just makes it visible.
# Its files live in the LangGraph state for this run, not on disk.
agent = create_deep_agent(
    model=MODEL,
    backend=StateBackend(),
    system_prompt=(
        "You are a file assistant. Use ls, read_file and edit_file to work "
        "with the user's notes. Keep replies to one sentence."
    ),
)

# %% Step 4: Run — note the seed files go in the INVOKE INPUT, not the constructor
# The agent reads state, so `files` is passed alongside `messages`.
task = (
    "List the files you can see, read /notes/todo.md, then append the line "
    "'- [ ] record episode 5' to the end of that file."
)
result = agent.invoke({"messages": [{"role": "user", "content": task}], "files": seed_files})

# %% Step 5: Which filesystem tools did it reach for?
print("\n[bold cyan]Filesystem tool calls:[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        print(f"  [green]{call['name']}[/green] {call['args']}")

# %% Step 6: Read the modified file back OUT of the returned state
# The updated filesystem comes back under result["files"] — same shape as the seed.
print("\n[bold cyan]/notes/todo.md after the run:[/bold cyan]")
final_content = result["files"]["/notes/todo.md"]["content"]
print(f"[yellow]{final_content}[/yellow]")

print(f"[bold green]Final answer:[/bold green] {text_of(result['messages'][-1])}")

# %%
