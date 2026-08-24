"""
14 - Filesystem Permissions
===========================
- `FilesystemPermission` rules control what the agent may read and write
- Rules are evaluated FIRST MATCH WINS, so order them specific -> general
- Three modes: allow, deny, and interrupt (ask a human — see episode 13)

Run:  python 14-permissions.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.utils import create_file_data
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


# %% Step 2: Seed a filesystem with something worth protecting
seed_files = {
    "/secrets/api_key.md": create_file_data("PROD_KEY=do-not-change-me\n"),
    "/notes/scratch.md": create_file_data("# Scratch\n"),
}

# %% Step 3: Write the rule list
# Two rules of the road:
#   - every path must be absolute (start with "/"); use ** to match recursively
#   - anything no rule matches is ALLOWED, so you only write the restrictions
# ORDER MATTERS: the first matching rule wins, so put specific rules first.
permissions = [
    # Nothing may be WRITTEN under /secrets/ (reads are untouched by this rule).
    FilesystemPermission(operations=["write"], paths=["/secrets/**"], mode="deny"),
]

print("[bold cyan]Rules (first match wins; unmatched = allowed):[/bold cyan]")
for index, rule in enumerate(permissions, start=1):
    print(f"  {index}. [magenta]{rule.mode:6}[/magenta] "
          f"{rule.operations} on {rule.paths}")

agent = create_deep_agent(
    model=MODEL,
    backend=StateBackend(),
    permissions=permissions,
    system_prompt="You are a file assistant. Attempt what is asked; report failures plainly.",
)


def attempt(task: str) -> dict:
    """Run one task against the seeded filesystem and report the tool results."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": task}], "files": seed_files}
    )
    for message in result["messages"]:
        if message.__class__.__name__ == "ToolMessage":
            snippet = text_of(message).strip().replace("\n", " ")[:90]
            print(f"    [dim]{message.name}[/dim] -> {snippet}")
    return result


# %% Step 4: Reading the protected file is allowed
# Rule 1 only covers "write", so a read falls through to rule 2.
print("\n[bold cyan]1. READ /secrets/api_key.md (expect: allowed)[/bold cyan]")
attempt("Read the file /secrets/api_key.md and tell me its contents.")

# %% Step 5: Writing to it is denied
# Rule 1 matches, mode="deny", so the tool call is refused before it runs.
print("\n[bold cyan]2. WRITE /secrets/api_key.md (expect: denied)[/bold cyan]")
denied = attempt("Overwrite /secrets/api_key.md with the text 'HACKED'.")
print(f"  [bold green]Agent says:[/bold green] {text_of(denied['messages'][-1]).strip()[:160]}")

# %% Step 6: Writing elsewhere still works
print("\n[bold cyan]3. WRITE /notes/scratch.md (expect: allowed)[/bold cyan]")
allowed = attempt("Append the line 'permissions are neat' to /notes/scratch.md.")
print(f"  [bold green]Agent says:[/bold green] {text_of(allowed['messages'][-1]).strip()[:160]}")

# %% Step 7: The third mode — interrupt
# mode="interrupt" does not allow or deny; it PAUSES for a human, using exactly
# the __interrupt__ / Command(resume=...) flow from episode 13. Use it for
# paths that are risky but sometimes legitimate.
print("\n[dim]Tip: mode='interrupt' asks a human instead of deciding (see ep. 13).[/dim]")

# %%
