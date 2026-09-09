"""
DeepCoder 07 - Approvals, Streamed
==================================
- A pause becomes just another event: ApprovalNeeded
- The renderer answers it and resumes the SAME turn, mid-stream
- This is the last CLI-only DeepCoder; Part 8 puts a real UI on these events

Run:  python main.py
"""

# %% Step 1: Imports and setup
import uuid

import config
import runner
from agent import build_agent
from rich import print


# %% Step 2: Ask the human about ONE pending action
def summarize(action: dict) -> str:
    """One readable line describing what the agent wants to do."""
    name = action.get("name", "?")
    args = action.get("args", {}) or {}
    if name == "execute":
        return f"run: {args.get('command', '')}"
    path = args.get("file_path") or args.get("path") or ""
    return f"{name}: {path}" if path else f"{name}({args})"


def decide(action: dict, allowlist: set[str]) -> dict:
    """Return a decision dict for a single pending tool call."""
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


# %% Step 3: Render one turn's events as they arrive
def ask(agent, question: str, thread_id: str, allowlist: set[str]) -> None:
    """Stream a turn, printing events live and handling approval pauses."""
    config_dict = {"configurable": {"thread_id": thread_id}}
    payload = {"messages": [{"role": "user", "content": question}]}
    streaming = False  # have we printed the "deepcoder >" header yet?
    # Shared across pauses so an approved tool call is not announced twice.
    seen: set[str] = set()

    while True:
        pending: list[dict] | None = None

        for event in runner.run_turn(agent, payload, config_dict, seen):
            match event:
                case runner.ToolStart(name=name, args=args):
                    print(f"\n  [magenta]* {summarize({'name': name, 'args': args})}[/magenta]")
                    streaming = False

                case runner.Token(text=text):
                    if not streaming:
                        print("\n[bold cyan]deepcoder >[/bold cyan] ", end="")
                        streaming = True
                    # end="" keeps tokens on one flowing line, like a chat UI.
                    print(text, end="")

                case runner.ApprovalNeeded(actions=actions):
                    print()
                    pending = actions

                case runner.Done(text=text, usage=usage):
                    if not text and not streaming:
                        print("\n[dim](done — no closing message)[/dim]")
                    if usage:
                        print(f"\n[dim]tokens: {usage.get('total_tokens', '?')}[/dim]")
                    print()
                    return

                case runner.Failed(error=error):
                    print(f"\n[red]error:[/red] {error}\n")
                    return

        if pending is None:
            return
        # Answer every pending action, then resume the same turn.
        payload = runner.resume_with([decide(action, allowlist) for action in pending])


# %% Step 4: The REPL
BANNER = """[bold cyan]DeepCoder[/bold cyan] [dim]— part 7, streamed approvals[/dim]
[dim]Risky tools ask first, without stopping the stream.[/dim]
[dim]/new resets, /exit quits.[/dim]"""


def main() -> None:
    """Read a line, stream the answer, repeat."""
    agent = build_agent()
    thread_id = uuid.uuid4().hex[:8]
    allowlist: set[str] = set()

    print(BANNER)
    print(f"[dim]{config.describe()}[/dim]\n")

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
            ask(agent, question, thread_id, allowlist)
        except KeyboardInterrupt:
            print("\n[yellow]cancelled[/yellow]\n")


if __name__ == "__main__":
    main()
