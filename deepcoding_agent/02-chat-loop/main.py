"""
DeepCoder 02 - A Chat Loop With Memory
======================================
- A REPL keeps the conversation going instead of exiting after one answer
- A checkpointer + thread_id is what makes the agent remember earlier turns
- `/new` starts a fresh thread; `/exit` quits

Run:  python main.py
"""

# %% Step 1: Imports and setup
import os
import uuid

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from rich import print
from rich.markdown import Markdown

load_dotenv()
MODEL = os.getenv("DEEPCODER_MODEL", "ollama:qwen3.5:9b")


# %% Step 2: Normalize message content
def text_of(message) -> str:
    """Return a message's text, whether the provider sends a string or blocks."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 3: Build the agent WITH a checkpointer
# A checkpointer saves the graph's state after every step. Without one, each
# .invoke() starts from an empty message list and the agent has amnesia.
# InMemorySaver keeps that state in RAM — good enough until Part 13 swaps in
# SQLite so sessions survive a restart.
SYSTEM_PROMPT = """You are DeepCoder, a terminal coding assistant.
Answer concisely. Prefer short code examples over long prose.
When you are unsure about a file's contents, read it rather than guessing."""

agent = create_deep_agent(
    model=MODEL,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)


# %% Step 4: One turn of conversation
def ask(question: str, thread_id: str) -> str:
    """Send one message on a given thread and return the agent's reply.

    The thread_id is the memory key. Same id -> the agent sees the whole prior
    conversation. New id -> a blank slate.
    """
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [{"role": "user", "content": question}]}, config=config)
    return text_of(result["messages"][-1]).strip()


# %% Step 5: The REPL
BANNER = """[bold cyan]DeepCoder[/bold cyan] [dim]— part 2, chat loop[/dim]
[dim]/new resets the conversation, /exit quits, Ctrl-C interrupts.[/dim]"""


def main() -> None:
    """Read a line, send it to the agent, print the reply, repeat."""
    thread_id = uuid.uuid4().hex[:8]
    print(BANNER)
    print(f"[dim]model: {MODEL}  thread: {thread_id}[/dim]\n")

    while True:
        try:
            question = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            # Ctrl-D or Ctrl-C at the prompt is a normal way to leave.
            print("\n[dim]bye[/dim]")
            return

        if not question:
            continue
        if question in ("/exit", "/quit"):
            print("[dim]bye[/dim]")
            return
        if question == "/new":
            # A brand-new thread_id is all it takes to forget everything.
            thread_id = uuid.uuid4().hex[:8]
            print(f"[yellow]new conversation[/yellow] [dim]thread: {thread_id}[/dim]\n")
            continue

        try:
            answer = ask(question, thread_id)
        except KeyboardInterrupt:
            # Ctrl-C during a slow model call cancels the turn, not the app.
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
