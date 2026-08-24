"""
DeepCoder 06 - Streaming
========================
- runner.py turns the raw graph stream into small typed events
- The answer now appears token by token instead of after a long silence
- Approvals are switched OFF here so the stream stays the only new idea;
  Part 7 brings them back through the event layer

Run:  python main.py
"""

# %% Step 1: Imports and setup
import uuid

import config
import runner
from agent import build_agent
from rich import print


# %% Step 2: Describe a tool call in one line
def summarize(action: dict) -> str:
    """One readable line describing what the agent wants to do."""
    name = action.get("name", "?")
    args = action.get("args", {}) or {}
    if name == "execute":
        return f"run: {args.get('command', '')}"
    path = args.get("file_path") or args.get("path") or ""
    return f"{name}: {path}" if path else f"{name}({args})"


# %% Step 3: Render one turn's events as they arrive
def ask(agent, question: str, thread_id: str) -> None:
    """Stream a turn, printing each event the moment it arrives."""
    config_dict = {"configurable": {"thread_id": thread_id}}
    payload = {"messages": [{"role": "user", "content": question}]}
    streaming = False  # have we printed the "deepcoder >" header yet?

    for event in runner.run_turn(agent, payload, config_dict):
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

            case runner.Done(text=text, usage=usage):
                if not text and not streaming:
                    print("\n[dim](done — no closing message)[/dim]")
                if usage:
                    print(f"\n[dim]tokens: {usage.get('total_tokens', '?')}[/dim]")
                print()


# %% Step 4: The REPL
BANNER = """[bold cyan]DeepCoder[/bold cyan] [dim]— part 6, streaming[/dim]
[bold red]approvals are off in this part — use a throwaway workdir[/bold red]
[dim]/new resets, /exit quits.[/dim]"""


def main() -> None:
    """Read a line, stream the answer, repeat."""
    agent = build_agent()
    thread_id = uuid.uuid4().hex[:8]

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
            print(f"[yellow]new conversation[/yellow] [dim]thread: {thread_id}[/dim]\n")
            continue

        try:
            ask(agent, question, thread_id)
        except KeyboardInterrupt:
            print("\n[yellow]cancelled[/yellow]\n")


if __name__ == "__main__":
    main()
