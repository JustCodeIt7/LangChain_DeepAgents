"""
Episode 6 — Permission Gating: Human-in-the-Loop
================================================

The agent can no longer mutate the workspace or run destructive commands
without asking first. We use Deep Agents' built-in HumanInTheLoopMiddleware
via `create_deep_agent(interrupt_on=..., checkpointer=...)`.

When the model calls a gated tool, the graph PAUSES. We inspect state,
prompt the viewer y/n, and resume with `Command(resume={"decisions": [...]})`.

Two new pieces:
  1. `classify(command)` — regex risk triage that labels the prompt
     red/yellow/green so the viewer sees risk at a glance.
  2. `run_with_approval(agent, prompt, thread_id)` — the full interrupt/resume
     loop: invoke → if paused, ask → resume → repeat.

Builds on: Episodes 1-5 (model, agent, FilesystemBackend, run_shell).

Run:
    CODEIT_WORKDIR=./workspace python tutorial.py \
        "Create a file then delete it with rm. Show me each step."

Requires: pip install deepagents langchain-ollama rich.
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import os  # Environment variable access for provider/model/workdir config
import re  # Regular expressions — used by classify() to match safe/destructive patterns
import sys  # Command-line argument parsing (sys.argv[1])
from pathlib import Path  # Object-oriented filesystem paths with .resolve()

# Deep Agents harness — the core framework that compiles a LangGraph agent.
from deepagents import create_deep_agent  # Creates compiled agent graph
from deepagents.backends import FilesystemBackend  # Built-in fs tools: ls/read/write/edit/glob/grep

# LangChain — provider-agnostic LLM integration and tool definitions.
from langchain.chat_models import init_chat_model  # One call, any provider
from langchain.tools import tool  # Decorator → LLM-callable Tool

# LangChain Core — type hints for model and message objects.
from langchain_core.language_models import BaseChatModel  # Return type of get_model()
from langchain_core.messages import AIMessage  # Message type with tool_calls

# ─────────────────────────────────────────────────────────────────────────────
# LangGraph — state persistence and interrupt/resume primitives.
# MemorySaver is REQUIRED for interrupts to work: without it, Command(resume=...)
# has nowhere to resume from because there's no checkpointer storing the graph state.
# ─────────────────────────────────────────────────────────────────────────────
from langgraph.checkpoint.memory import (
    MemorySaver,
)  # In-process checkpointer — REQUIRED for interrupts
from langgraph.types import Command  # Resume primitive: Command(resume={"decisions":[...]})

# Rich — colored, live terminal output for the streaming view.
from rich.console import Console  # Renders [color] tags + handles input()

console = Console()  # Single shared console instance; reused across all print calls in this script


def get_model() -> BaseChatModel:
    """Build a chat model from env vars. Provider-agnostic via init_chat_model.

    This is the Episode 1 model factory, inlined for self-containment.
    The pattern: read LLM_PROVIDER → branch on provider → call init_chat_model
    with the right kwargs. We pre-build so WE own error messages (e.g., a clear
    'OPENAI_API_KEY required' instead of a cryptic stack trace from deep inside
    LangChain).

    Env vars consumed:
      - LLM_PROVIDER  : "ollama" (default) or "openai"
      - LLM_MODEL     : model name, e.g. "qwen2.5-coder:7b" or "gpt-4o-mini"
      - OPENAI_API_KEY: required when provider == "openai"
      - OLLAMA_BASE_URL: defaults to http://localhost:11434
    """
    # Read the provider selector — this is the single switch that determines
    # which branch of init_chat_model we take. Everything else flows from here.
    provider = os.getenv("LLM_PROVIDER", "ollama")

    # The model name comes from LLM_MODEL, defaulting to a small local Ollama
    # model so viewers can run the demo without an API key.
    name = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")

    if provider == "openai":
        # OpenAI requires an API key — we validate it HERE, before calling
        # init_chat_model, so the error message is clear and actionable.
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY required when LLM_PROVIDER=openai.")

        return init_chat_model(model=name, model_provider="openai")

    # Default: Ollama (local LLM server). We pass base_url so viewers can point
    # at a remote Ollama instance if needed (e.g., in a VM or container).
    return init_chat_model(
        model=name,
        model_provider="ollama",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. A demo tool to gate — reuses Ep 5's run_shell shape (trimmed for space).
#    This is the same dangerous shell execution from Episode 5, but now it goes
#    through the approval gate: interrupt_on={"run_shell": True} in build_agent().
# ─────────────────────────────────────────────────────────────────────────────


@tool
def run_shell(command: str) -> str:
    """Run a shell command in the workspace. Use for tests, installs, git."""
    import subprocess  # Imported locally to keep top-level imports clean; stdlib, no install needed

    cwd = str(Path(os.getenv("CODEIT_WORKDIR", "./workspace")).resolve())

    try:
        proc = subprocess.run(
            command,
            shell=True,  # Execute via /bin/sh -c (enables pipes/redirects)
            cwd=cwd,  # Confine working directory to the sandbox root
            capture_output=True,  # Capture stdout and stderr separately
            text=True,  # Return strings, not bytes
            timeout=120,  # Kill after 2 minutes — prevents hanging commands
        )
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    return f"$ {command}\n[exit {proc.returncode}]\n{proc.stdout or ''}{proc.stderr or ''}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. classify() — regex triage that LABELS the prompt. The interrupt itself
#    comes from interrupt_on; classify() is purely for display (coloring).
#
#    WHY TWO MECHANISMS? interrupt_on PAUSES execution before a tool runs.
#    classify() only COLORS the approval prompt so viewers see risk at a glance:
#      green = safe, yellow = needs-approval, red = blocked (never allowed)
# ─────────────────────────────────────────────────────────────────────────────

# SAFE_PATTERNS: commands that are read-only or low-risk. These auto-approve
# in interactive mode (the viewer still sees them but doesn't need to type 'y').
SAFE_PATTERNS = [
    r"^\s*ls\b",
    r"^\s*cat\b",
    r"^\s*pwd\b",
    r"^\s*echo\b",
    r"^\s*git status\b",
    r"^\s*git diff\b",
    r"^\s*pytest\b",
]

# DESTRUCTIVE_PATTERNS: commands that could cause irreversible damage. These
# are BLOCKED entirely — the agent cannot run them even with approval.
DESTRUCTIVE_PATTERNS = [
    r"rm\s+-rf?\b",
    r"git\s+push\s+.*-f",
    r"git\s+reset\s+--hard",
    r"\bdd\b",
    r"\bmkfs\b",
    r"curl.*\|\s*sh",
    r"wget.*\|\s*sh",
]


def classify(command: str) -> str:
    """Return 'safe', 'needs-approval', or 'blocked' for a shell command.

    Uses regex matching to categorize commands by danger level.
    The classification is used ONLY for display (coloring the approval prompt); the actual pausing
    comes from interrupt_on in build_agent().

    Returns:
        'blocked'         — destructive command, never allowed
        'safe'            — read-only/low-risk, auto-approved in interactive mode
        'needs-approval'  — everything else, requires explicit user approval
    """
    # Check destructive patterns FIRST — if a command matches any of these,
    # it's blocked regardless of what safe patterns might also match.
    for pat in DESTRUCTIVE_PATTERNS:
        if re.search(pat, command):
            return "blocked"

    # Then check safe patterns — these are common read-only commands that
    # don't need approval (ls, cat, echo, git status, etc.).
    for pat in SAFE_PATTERNS:
        if re.search(pat, command):
            return "safe"

    # Everything else requires explicit user approval before execution.
    return "needs-approval"


# ─────────────────────────────────────────────────────────────────────────────
# 3. build_agent — interrupt_on + MemorySaver. Our policy: gate shell + writes.
#    This is the core of Episode 6: we tell Deep Agents which tools require human
#    approval before execution, and provide a checkpointer so state persists across resume.
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {"run_shell": True, "write_file": True, "edit_file": True, "delete": True}


def build_agent(workdir: str | None = None):
    """Build the Deep Agent with human-in-the-loop approval gate.

    This is where Episode 6's key innovation lives: interrupt_on + MemorySaver.
    - interrupt_on tells Deep Agents which tools to PAUSE on before execution.
      When the model calls a gated tool, the graph pauses and waits for our decision.
    - checkpointer=MemorySaver() stores state so we can resume after approval.

    ⚠️ CRITICAL: Without MemorySaver (or another checkpointer), interrupts DON'T WORK —
       Command(resume=...) has nowhere to save/restore state from. This is a common gotcha.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph with approval gate enabled.
    """
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    # Create the workspace directory if it doesn't exist yet — ensures sandbox is ready
    root.mkdir(parents=True, exist_ok=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[run_shell],  # Custom tool: run shell commands in workspace (Ep 5)
        system_prompt="You are CodeIt, a coding agent. The user approves destructive actions.",
        backend=FilesystemBackend(  # Built-in filesystem tools with sandbox ON
            root_dir=str(root),  # Confine all file ops to this directory
            virtual_mode=True,  # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        interrupt_on=INTERRUPT_ON,  # ← pause before these tools — human must approve
        checkpointer=MemorySaver(),  # ← REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. run_with_approval — invoke → if paused, ask → resume → repeat.
#    This is the human-in-the-loop driver that makes Episode 6's safety gate real.
# ─────────────────────────────────────────────────────────────────────────────


def _config(thread_id: str) -> dict:
    """Build the LangGraph config dict with thread ID + recursion limit.

    - configurable.thread_id: groups related turns into a conversation thread
      (required for MemorySaver to persist state across resume).
    - recursion_limit: caps total super-steps so a looping model can't hang.
      Default 25 × 2 = 50 (each step ≈ 2 super-steps: model call + tool exec).
    """
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": int(os.getenv("CODEIT_MAX_ITERS", "25")) * 2,
    }


def _print_event(chunk) -> None:
    """Pretty-print one v2 stream chunk to the console.

    V2 chunks are dicts with keys: type, ns (node namespace), data.
    We only care about 'updates' — each update contains a snapshot of node state.
    For each message in that state, we render tool calls and assistant text.
    """
    if chunk.get("type") != "updates":  # Skip non-update chunks (e.g., 'values')
        return

    for _n, state in chunk.get("data", {}).items():  # Iterate over node states in this update
        if not isinstance(state, dict):  # Some nodes aren't message-based — skip them
            continue
        for msg in state.get("messages", []):  # Each node may have multiple messages
            if isinstance(msg, AIMessage) and msg.tool_calls:  # Model decided to call a tool
                for tc in msg.tool_calls:
                    console.print(f"[cyan]tool call:[/cyan] {tc['name']}({tc['args']})")
            elif isinstance(msg, AIMessage) and msg.content:  # Plain text response from the model
                console.print(f"[green]assistant:[/green] {msg.content}")


def _pending_tool_call(state) -> tuple[str, dict] | None:
    """Read (name, args) of the tool call the model just requested.

    When interrupt_on pauses the agent, state.next is non-empty — meaning the
    graph is waiting for a Command(resume=...) to proceed. This helper extracts
    which tool was called and with what arguments, so we can show it to the user.

    We scan messages in REVERSE order (newest first) because the pending tool
    call is always the most recent AIMessage with tool_calls set.
    """
    for msg in reversed(getattr(state, "values", {}).get("messages", []) or []):
        if getattr(msg, "tool_calls", None):  # This message has one or more tool calls
            return msg.tool_calls[-1]["name"], msg.tool_calls[-1]["args"]
    return None


def run_with_approval(agent, prompt: str, thread_id: str = "default") -> dict:
    """invoke → if interrupted, await_approval → resume. Loops until done.

    This is the human-in-the-loop driver from Episode 6. The flow:
      1. Stream the agent's response (prints live via _print_event)
      2. Check if state.next is non-empty (agent paused on an interrupt)
      3. If so, extract the pending tool call and ask for approval
      4. Resume with Command(resume={"decisions": [{"type": "approve"}]}) or reject
      5. Repeat until no more interrupts

    The loop handles MULTIPLE sequential approvals — e.g., if the agent needs to
    run three shell commands in a row, each one triggers its own approval prompt.

    Args:
        agent: The compiled Deep Agents graph from build_agent().
        prompt: Initial task for the agent (e.g., "Run: echo hello").
        thread_id: Conversation thread ID — must match across stream/resume calls.

    Returns: Final agent state dict with messages and values.
    """
    config = _config(thread_id)
    auto = os.getenv("CODEIT_AUTO_APPROVE", "false").lower() == "true"  # --yolo mode

    # Phase 1: Stream the initial response — this runs until the agent either
    # completes or hits an interrupt_on tool. If it pauses, state.next will be set.
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": prompt}]},
        config=config,
        stream_mode="updates",
        version="v2",
    ):
        _print_event(chunk)

    state = agent.get_state(config)  # Get the current graph state after streaming

    # Phase 2: Handle interrupts — loop while the agent is paused waiting for approval.
    # state.next being non-empty means there's a pending interrupt to resolve.
    while state.next:  # paused on an interrupt
        pending = _pending_tool_call(state)
        if pending is None:
            console.print("[red]Interrupt with no recognizable tool call — aborting.[/red]")
            break

        name, args = pending

        if auto:
            # --yolo mode: skip the prompt and approve everything automatically.
            console.print("[yellow]--yolo: auto-approving[/yellow]")
            cmd = Command(resume={"decisions": [{"type": "approve"}]})
        else:
            # Interactive mode: classify risk, show colored prompt, ask user for approval.
            risk = classify(args.get("command", "")) if name == "run_shell" else "needs-approval"
            color = {"safe": "green", "needs-approval": "yellow", "blocked": "red"}[risk]
            console.print(f"[{color}]risk: {risk}[/{color}]  tool: {name}  args: {args}")

            # Block destructive commands even in interactive mode — the user can't approve.
            if risk == "blocked":
                console.print("[red]Blocked command — cannot approve.[/red]")
                cmd = Command(
                    resume={
                        "decisions": [{"type": "reject", "message": "Command blocked by policy."}]
                    }
                )
            else:
                answer = console.input("[bold]Approve? (y/n): [/bold]").strip().lower()
                if answer == "y":
                    # Approve: let the tool execute and continue.
                    cmd = Command(resume={"decisions": [{"type": "approve"}]})
                else:
                    # Reject: tell the agent this action was denied, it should try another approach.
                    cmd = Command(
                        resume={
                            "decisions": [{"type": "reject", "message": "User denied this action."}]
                        }
                    )

        # Resume the graph with our decision — stream the result and check for more interrupts.
        for chunk in agent.stream(cmd, config=config, stream_mode="updates", version="v2"):
            _print_event(chunk)
        state = agent.get_state(config)  # Re-check: did we hit another interrupt?

    return state.values


def main() -> None:
    """Entry point — build the agent with approval gate and run it.

    The demo prompt asks the agent to create a file then delete it, demonstrating how
    each mutating action triggers an approval prompt that the viewer must accept or reject.
    """
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Run: echo hello"

    agent = build_agent()
    state = run_with_approval(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


if __name__ == "__main__":
    main()
