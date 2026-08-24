"""
13 - Human in the Loop (Approvals)
==================================
- `interrupt_on` pauses the agent BEFORE a risky tool runs
- The run stops and returns `result["__interrupt__"]` describing what it wants
- You resume with `Command(resume={"decisions": [...]})`
- Requires a checkpointer — the paused run has to be stored somewhere

Run:  python 13-human_in_the_loop.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command  # carries the human's decision back in
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 2: A tool with real-world consequences
def send_email(to: str, body: str) -> str:
    """Send an email to a recipient.

    Args:
        to: The recipient's email address.
        body: The body text of the email.
    """
    return f"Email delivered to {to}"


# %% Step 3: Gate that tool behind human approval
# interrupt_on maps tool name -> True (all four decision types allowed) or an
# InterruptOnConfig dict such as {"allowed_decisions": ["approve", "reject"]}.
agent = create_deep_agent(
    model=MODEL,
    tools=[send_email],
    interrupt_on={"send_email": True},
    checkpointer=InMemorySaver(),  # REQUIRED: the pause must be persisted
    system_prompt="You are an assistant. Use send_email when asked. Be brief.",
)


# %% Step 4: A helper that runs, inspects the pause, and resumes
def run_with_decision(decision: dict, thread_id: str) -> None:
    """Start a run, show what the agent wants to do, then apply `decision`.

    Each call uses a FRESH thread_id — reusing one would resume the previous,
    already-resolved run instead of triggering a new interrupt.
    """
    config = {"configurable": {"thread_id": thread_id}}
    request = "Email alice@example.com saying the report is ready."
    result = agent.invoke({"messages": [{"role": "user", "content": request}]}, config=config)

    # The pause shows up as "__interrupt__" in the returned state.
    interrupts = result.get("__interrupt__")
    if not interrupts:
        print("  [yellow]No interrupt fired — the agent never called the tool.[/yellow]")
        return

    for action in interrupts[0].value["action_requests"]:
        print(f"  [bold]paused before:[/bold] [green]{action['name']}[/green]({action['args']})")

    # Resume. "decisions" is a LIST, one entry per pending action request.
    print(f"  [bold]human decides:[/bold] [magenta]{decision['type']}[/magenta]")
    resumed = agent.invoke(Command(resume={"decisions": [decision]}), config=config)
    print(f"  [bold]outcome:[/bold] {text_of(resumed['messages'][-1]).strip()}\n")


# %% Step 5: Approve — the tool runs with the original arguments
print("[bold cyan]1. APPROVE[/bold cyan]")
run_with_decision({"type": "approve"}, thread_id="approve-run")

# %% Step 6: Reject — the tool is skipped and your message goes back to the model
print("[bold cyan]2. REJECT[/bold cyan]")
run_with_decision(
    {"type": "reject", "message": "Do not email anyone. Draft it for me instead."},
    thread_id="reject-run",
)

# %% Step 7: The other two decision types
# Same mechanism, different payloads — swap either into run_with_decision():
#
#   edit    -> run the tool, but with arguments YOU supply:
#              {"type": "edit",
#               "edited_action": {"name": "send_email",
#                                 "args": {"to": "bob@example.com", "body": "..."}}}
#
#   respond -> skip the tool and feed your own text back as its result:
#              {"type": "respond", "message": "Already sent it myself."}
print("[dim]See Step 7 in the source for the 'edit' and 'respond' payloads.[/dim]")

# %%
