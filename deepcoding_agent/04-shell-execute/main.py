"""
DeepCoder 04 - Running Shell Commands
=====================================
- LocalShellBackend adds an `execute` tool: the agent can run your tests
- inherit_env=True is required, or PATH is empty and every command fails
- Nothing is gated yet: whatever the model decides to run, runs

Run:  python main.py
"""

# %% Step 1: Imports and setup
import uuid

import config
from agent import build_agent
from rich import print
from rich.markdown import Markdown


# %% Step 2: Normalize message content
def text_of(message) -> str:
    """Return a message's text, whether the provider sends a string or blocks."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 3: One turn of conversation
def ask(agent, question: str, thread_id: str) -> str:
    """Send one message on a given thread and return the agent's reply.

    Small local models sometimes finish a turn on the tool call itself and
    leave the final message empty. Say so, rather than printing nothing and
    looking broken. Part 6 fixes this properly by streaming the tool calls
    as they happen, so there is always something to watch.
    """
    config_dict = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]}, config=config_dict
    )
    return text_of(result["messages"][-1]).strip() or "_(done — no closing message)_"


# %% Step 4: The REPL
BANNER = """[bold cyan]DeepCoder[/bold cyan] [dim]— part 4, shell access[/dim]
[dim]The agent can now run shell commands. There are no guardrails yet.[/dim]
[dim]/new resets the conversation, /exit quits.[/dim]"""


def main() -> None:
    """Read a line, send it to the agent, print the reply, repeat."""
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
            answer = ask(agent, question, thread_id)
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
