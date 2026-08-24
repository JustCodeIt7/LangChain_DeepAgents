"""
16 - Skills (Reusable Expertise on Demand)
==========================================
- A skill is a folder with a SKILL.md: YAML frontmatter + markdown instructions
- Progressive disclosure: the agent sees only name+description up front...
- ...and reads the full file ONLY when the task actually calls for it

Run:  python 16-skills.py
"""

# %% Step 1: Imports and setup
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend  # skills are read THROUGH the backend
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


# %% Step 2: Point at the skills directory
# Layout on disk:
#   skills/
#     release-notes/
#       SKILL.md      <- frontmatter (name, description) + instructions
EPISODE_DIR = Path(__file__).parent
skill_file = EPISODE_DIR / "skills" / "release-notes" / "SKILL.md"

print("[bold cyan]Skill package:[/bold cyan]")
print(f"  [yellow]{skill_file.relative_to(EPISODE_DIR)}[/yellow]")
print(f"  {len(skill_file.read_text().splitlines())} lines of instructions")

# %% Step 3: Register the skills directory
# GOTCHA: skills are read THROUGH the agent's backend, not off the host OS.
# The default StateBackend is a virtual filesystem and cannot see your disk, so
# skills would silently never load. Use a real backend, and give the skills path
# as the backend sees it ("/skills"), not as an OS path.
backend = FilesystemBackend(root_dir=str(EPISODE_DIR), virtual_mode=True)

# Only the frontmatter (name + description) is injected into the system prompt.
# The body stays on disk until the agent decides it needs it — that is what
# keeps a library of 50 skills from blowing up your context window.
agent = create_deep_agent(
    model=MODEL,
    backend=backend,
    skills=["/skills"],
    system_prompt="You are a release manager. Use your skills when they apply.",
)

# %% Step 4: Give it a task the skill covers
# We never mention the skill by name — the agent matches the request against
# the skill's description on its own.
changes = (
    "- added dark mode toggle\n"
    "- fixed crash when opening empty projects\n"
    "- renamed the 'Sync' button to 'Refresh'"
)
task = f"Write release notes for version 2.1.0 from these changes:\n{changes}"
result = agent.invoke({"messages": [{"role": "user", "content": task}]})

# %% Step 5: Watch progressive disclosure happen
# You should see a read_file call for SKILL.md BEFORE the answer — that is the
# agent pulling in the full instructions only once it knew they were relevant.
print("\n[bold cyan]Tool calls (look for the SKILL.md read):[/bold cyan]")
for message in result["messages"]:
    for call in getattr(message, "tool_calls", []) or []:
        target = call["args"].get("file_path", "")
        marker = " [green]<- loading the skill[/green]" if "SKILL.md" in str(target) else ""
        print(f"  {call['name']} [yellow]{target}[/yellow]{marker}")

# %% Step 6: The output should follow the skill's house style
print("\n[bold cyan]Result (note the format the skill dictated):[/bold cyan]")
print(text_of(result["messages"][-1]))

# %%
