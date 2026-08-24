"""
DeepCoder 05 - Asking Permission
================================
- `interrupt_on` pauses the agent BEFORE a risky tool runs
- ONE pause can carry SEVERAL pending tool calls, so decisions is a LIST
- "always" adds a tool to a session allowlist so you stop being asked

Run:  python main.py
"""

# %% Step 1: Imports and setup
import uuid

import config
from agent import build_agent
from langgraph.types import Command
from rich import print
from rich.markdown import Markdown


# %% Step 2: Normalize message content
def text_of(message) -> str:
    """Return a message's text, whether the provider sends a string or blocks."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


def summarize(action: dict) -> str:
    """One readable line describing what the agent wants to do."""
    name = action.get("name", "?")
    args = action.get("args", {}) or {}
    if name == "execute":
        return f"run: {args.get('command', '')}"
    path = args.get("file_path") or args.get("path") or ""
    return f"{name}: {path}" if path else f"{name}({args})"


# %% Step 3: Ask the human about ONE pending action
def decide(action: dict, allowlist: set[str]) -> dict:
    """Return a decision dict for a single pending tool call.

    The four decision types deepagents understands are approve, reject, edit
    and respond. We use the first two, plus a local "always" shortcut that
    just means "approve, and stop asking me about this tool".
    """
    name = action.get("name", "?")
    if config.AUTO_APPROVE or name in allowlist:
        print(f"  [dim]auto-approved:[/dim] {summarize(action)}")
        return {"type": "approve"}

    print(f"  [bold yellow]?[/bold yellow] {summarize(action)}")
    while True:
        answer = input("    [y]es / [n]o / [a]lways > ").strip().lower()
        if answer in ("y", "yes", ""):
            return {"type": "approve"}
        if answer in ("n", "no"):
            reason = input("    why not (optional) > ").strip()
            return {"type": "reject", "message": reason or "The user declined this action."}
        if answer in ("a", "always"):
            allowlist.add(name)
            return {"type": "approve"}


# %% Step 4: Run a turn, pausing for approval as often as needed
def ask(agent, question: str, thread_id: str, allowlist: set[str]) -> str:
    """Send one message, resolving every approval pause until the turn ends.

    A single turn can pause more than once (approve a write, the model then
    wants to run tests), so this is a loop, not one check.
    """
    config_dict = {"configurable": {"thread_id": thread_id}}
    payload = {"messages": [{"role": "user", "content": question}]}

    while True:
        result = agent.invoke(payload, config=config_dict)
        interrupts = result.get("__interrupt__")
        if not interrupts:
            return text_of(result["messages"][-1]).strip() or "_(done — no closing message)_"

        # THE KEY DETAIL: one interrupt bundles EVERY gated call from that
        # model turn. Build one decision per action, in the same order --
        # a mismatched length raises ValueError deep inside the graph.
        actions = interrupts[0].value["action_requests"]
        decisions = [decide(action, allowlist) for action in actions]

        # Resuming replaces the input entirely: send the Command, not the
        # original question, or you will ask it twice.
        payload = Command(resume={"decisions": decisions})


# %% Step 5: The REPL
BANNER = """[bold cyan]DeepCoder[/bold cyan] [dim]— part 5, approvals[/dim]
[dim]Risky tools now ask first. /new resets, /exit quits.[/dim]"""


def main() -> None:
    """Read a line, send it to the agent, print the reply, repeat."""
    agent = build_agent()
    thread_id = uuid.uuid4().hex[:8]
    allowlist: set[str] = set()  # tools the user said "always" to, this session

    print(BANNER)
    print(f"[dim]{config.describe()}  gated: {', '.join(config.GATED_TOOLS)}[/dim]")
    if config.AUTO_APPROVE:
        print("[bold red]auto-approve is ON — nothing will ask permission[/bold red]")
    print()

    while True:
        try:
            question = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[dim]bye[/dim]")
            return

        if not question:
            continue
        if question in ("/exit", "/quit"):
            print("[dim]bye[/dim]")
            return
        if question == "/new":
            thread_id = uuid.uuid4().hex[:8]
            allowlist.clear()
            print(f"[yellow]new conversation[/yellow] [dim]thread: {thread_id}[/dim]\n")
            continue

        try:
            answer = ask(agent, question, thread_id, allowlist)
        except KeyboardInterrupt:
            print("\n[yellow]cancelled[/yellow]\n")
            continue
        except Exception as error:  # noqa: BLE001 - show the user any failure
            print(f"[red]error:[/red] {error}\n")
            continue

        print("\n[bold cyan]deepcoder >[/bold cyan]")
        print(Markdown(answer))
        print()


if __name__ == "__main__":
    main()
