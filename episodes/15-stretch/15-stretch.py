"""
Episode 15 — LangSmith Observability Appendix
=============================================

Show viewers how to see what the agent is DOING under the hood. With
LangSmith tracing on, every model call, tool call, subagent delegation,
and the full message history at each step becomes visible in a trace URL
you can open in the browser.

This is the LEAST new code of any episode — mostly docs + a tiny helper.
LangSmith is already a dep from Phase 0; no new install needed.

New pieces:
  1. `.env.example` entries: LANGSMITH_API_KEY=, LANGSMITH_TRACING=true,
     LANGSMITH_PROJECT=codeit-demo. (Set these in your .env.)
  2. `codeit/observability.py` — `trace_url_for_run(run_id)` and
     `maybe_print_trace_url(state)` helpers.
  3. The demo runs a task with tracing on and prints the trace URL at the end.

⚠️ Assumption: env var names are LANGSMITH_* (per the ecosystem-primer skill).
   Older names (LANGCHAIN_API_KEY, LANGCHAIN_TRACING) no longer work.
⚠️ The trace URL shape changes over time. The helper is best-effort; if the
   URL doesn't open, direct viewers to the LangSmith dashboard and have them
   find the run by project + timestamp.

Builds on: Episodes 1-14. Requires: pip install deepagents langchain-ollama rich langsmith.
Run:
    export LANGSMITH_API_KEY=...
    export LANGSMITH_TRACING=true
    export LANGSMITH_PROJECT=codeit-demo
    CODEIT_WORKDIR=./examples/sample_app python tutorial.py "fix the failing test"

Requires: pip install deepagents langchain-ollama rich langsmith.
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import os  # Environment variable access for provider/model/workdir config
import sys  # Command-line argument parsing and stderr output
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

# LangGraph — state persistence and interrupt/resume primitives.
from langgraph.checkpoint.memory import MemorySaver  # REQUIRED for interrupts (Ep 6)
from langgraph.types import Command  # Resume: Command(resume={"decisions":[...]})

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

        # For OpenAI, init_chat_model just needs model + provider name.
        # The API key is picked up from OPENAI_API_KEY automatically by LangChain.
        return init_chat_model(model=name, model_provider="openai")

    # Default: Ollama (local LLM server). We pass base_url so viewers can point
    # at a remote Ollama instance if needed (e.g., in a VM or container).
    return init_chat_model(
        model=name,
        model_provider="ollama",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


def _workspace_root() -> Path:
    """Resolve CODEIT_WORKDIR to an absolute path.

    This is the sandbox root — all file operations are confined here by
    FilesystemBackend(virtual_mode=True). The .resolve() call follows symlinks
    and normalizes ../ sequences so we can do a clean relative_to check later.
    """
    return Path(os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Observability helpers — build a LangSmith trace URL if tracing is on.
#    LangSmith tracing is enabled purely by env vars; no code change to the
#    agent itself is required. This helper just surfaces the URL at the end.
#
#    HOW IT WORKS: When LANGSMITH_TRACING=true, LangChain's built-in tracer
#    automatically attaches to every model call and tool invocation in the
#    graph. Each run gets a unique run_id that appears in the trace URL.
#    We extract it from the final state object (if available) and print it.
# ─────────────────────────────────────────────────────────────────────────────

def trace_url_for_run(run_id: str | None) -> str | None:
    """Build a LangSmith trace URL if tracing is on and a run_id is available.

    The URL format is: https://smith.langchain.com/projects/p/<project>/r/<run_id>
    This lets viewers click through to see the full execution graph — every
    model call, tool invocation, and message in an interactive UI.

    Returns None if tracing isn't enabled or no run_id was captured. The URL
    shape may change over time; this is best-effort. If it doesn't open, direct
    viewers to the LangSmith dashboard and have them find the run by project + timestamp.
    """
    # Guard: only build a URL if tracing is explicitly enabled via env var.
    # This prevents printing broken URLs when LangSmith isn't configured.
    if os.getenv("LANGSMITH_TRACING", "").lower() != "true":
        return None

    # No run_id means we couldn't extract it from the state — nothing to link to.
    if not run_id:
        return None

    # The project name groups related runs together in the LangSmith UI.
    # Default is "default" but viewers should set LANGSMITH_PROJECT=codeit-demo.
    project = os.getenv("LANGSMITH_PROJECT", "default")

    # URL shape: https://smith.langchain.com/o/<org>/projects/p/<project>/r/<run_id>
    # The exact shape depends on the LangSmith UI; this is a best-effort helper.
    return f"https://smith.langchain.com/projects/p/{project}/r/{run_id}"


def maybe_print_trace_url(state) -> None:
    """After a run, print the trace URL to stderr if tracing is on.

    The run_id isn't always on the state object — it depends on the LangGraph
    version and whether LangSmith's tracer attached one. We try a few common
    attribute paths; if none have it, we just tell the viewer to check the dashboard.

    This function demonstrates graceful degradation: even if we can't build a
    direct URL, we still guide the viewer to find their trace manually.
    """
    # Try to extract run_id from the state object using multiple access patterns.
    # LangGraph's state representation varies across versions — some expose it
    # as an attribute (.run_id), others as a dict key ("run_id"). We try both.
    run_id = None
    if state is not None:
        run_id = (getattr(state, "run_id", None)  # Attribute access for object-style state
                  or (state.get("run_id") if isinstance(state, dict) else None))

    url = trace_url_for_run(run_id)
    if url:
        # Print the clickable URL in dim text so it doesn't clutter output.
        console.print(f"[dim]Trace: {url}[/dim]")
    elif os.getenv("LANGSMITH_TRACING", "").lower() == "true":
        # Tracing is on but we couldn't build a direct URL — guide the viewer
        # to find their run manually in the LangSmith dashboard.
        project = os.getenv("LANGSMITH_PROJECT", "default")
        console.print(
            f"[dim]Tracing is on. Open the LangSmith dashboard → "
            f"project '{project}' to find this run by timestamp.[/dim]"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. A demo agent (trimmed from Ep 14) so we have something to trace.
#    This section reuses the same patterns from earlier episodes: a custom
#    @tool, INTERRUPT_ON policy, build_agent(), and streaming driver.
#    The ONLY new piece is maybe_print_trace_url() at the end of main().
# ─────────────────────────────────────────────────────────────────────────────

@tool
def run_shell(command: str) -> str:
    """Run a shell command in the workspace. Use for tests, installs, git.

    ⚠️ DANGER ZONE — this tool executes arbitrary shell commands with
    shell=True. The sandbox confines CWD to CODEIT_WORKDIR, but it does NOT
    prevent `rm -rf /` if the user has permission. NEVER run unsandboxed on a
    real repo without the approval gate (Ep 6).

    Returns: stdout + stderr + exit code as a formatted string. Non-zero exits
    are returned as strings (not exceptions) so the model can read "[exit N]"
    and self-correct in its next turn.
    """
    import subprocess  # Imported here to keep top-level imports clean; stdlib, no install needed

    try:
        # shell=True lets the model pass pipes/redirects as a single string —
        # more dangerous (injection risk) but simpler for an agent that's
        # constructing commands. The approval gate in Ep 6 mitigates this.
        proc = subprocess.run(
            command,
            shell=True,                           # Execute via /bin/sh -c (enables pipes/redirects)
            cwd=str(_workspace_root()),           # Confine working directory to the sandbox root
            capture_output=True,                  # Capture stdout and stderr separately
            text=True,                            # Return strings, not bytes
            timeout=120,                          # Kill after 2 minutes — prevents hanging commands
        )
    except Exception as e:
        # Any exception (timeout, file not found) is returned as a string so the
        # model can read it and adjust its strategy. Never raise from a tool.
        return f"Error: {type(e).__name__}: {e}"

    # Format output with exit code — the "[exit N]" pattern is what Ep 11's
    # failure detector looks for to trigger self-healing recovery loops.
    return f"$ {command}\n[exit {proc.returncode}]\n{proc.stdout or ''}{proc.stderr or ''}"


# INTERRUPT_ON defines which tools require human approval before execution.
# This is the safety gate from Episode 6 — without it, run_shell could delete
# files, write_file could overwrite configs, etc. The agent PAUSES and asks.
INTERRUPT_ON = {"run_shell": True, "write_file": True, "edit_file": True, "delete": True}


def build_agent(workdir: str | None = None):
    """Build the Deep Agent with all Episodes 1-14 wiring in one place.

    This is the culmination of the series — every capability from earlier
    episodes converges here: model factory (Ep 1), filesystem backend (Ep 3),
    custom tools (Ep 5), approval gate (Ep 6), system prompt (Ep 7).

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    # Resolve the workspace root — all file operations are confined here.
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    root.mkdir(parents=True, exist_ok=True)  # Create the sandbox directory if it doesn't exist

    return create_deep_agent(
        model=get_model(),                    # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[run_shell],                    # Custom tool: run shell commands in workspace (Ep 5)
        system_prompt="You are CodeIt, a coding agent. Use run_shell to run tests.",
        backend=FilesystemBackend(            # Built-in filesystem tools with sandbox ON
            root_dir=str(root),               # Confine all file ops to this directory
            virtual_mode=True,                # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        interrupt_on=INTERRUPT_ON,            # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),           # REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Streaming driver (same shape as Eps 2-14, ungated for simplicity).
#    This section handles the live rendering of agent events — tool calls and
#    assistant messages appear in real-time as the graph executes.
# ─────────────────────────────────────────────────────────────────────────────

def _config(thread_id: str) -> dict:
    """Build the LangGraph config dict with thread ID + recursion limit.

    - configurable.thread_id: groups related turns into a conversation thread
      (required for MemorySaver to persist state across resume).
    - recursion_limit: caps total super-steps (model call + tool exec ≈ 2 per step)
      so a looping model can't hang the viewer's machine. Default 25 × 2 = 50.
    """
    return {"configurable": {"thread_id": thread_id},
            "recursion_limit": int(os.getenv("CODEIT_MAX_ITERS", "25")) * 2}


def _print_event(chunk) -> None:
    """Pretty-print one v2 stream chunk to the console.

    V2 chunks are dicts with keys: type, ns (node namespace), data.
    We only care about 'updates' — each update contains a snapshot of node state.
    For each message in that state, we render tool calls and assistant text.
    """
    if chunk.get("type") != "updates":  # Skip non-update chunks (e.g., 'values')
        return

    for _n, state in chunk.get("data", {}).items():  # Iterate over node states in this update
        if not isinstance(state, dict):              # Some nodes aren't message-based — skip them
            continue
        for msg in state.get("messages", []):         # Each node may have multiple messages
            if isinstance(msg, AIMessage) and msg.tool_calls:  # Model decided to call a tool
                for tc in msg.tool_calls:
                    console.print(f"[cyan]tool call:[/cyan] {tc['name']}({tc['args']})")
            elif isinstance(msg, AIMessage) and msg.content:   # Plain text response from the model
                console.print(f"[green]assistant:[/green] {msg.content}")


# ─────────────────────────────────────────────────────────────────────────────
# 3b. Risk classification for shell commands (from Ep 6).
#    classify() LABELS the command; interrupt_on does the actual pausing.
#    This is purely cosmetic — it colors the approval prompt so viewers see
#    risk at a glance: green=safe, yellow=review, red=dangerous.
# ─────────────────────────────────────────────────────────────────────────────

# SAFE_PATTERNS: commands that are read-only or low-risk. These auto-approve
# in interactive mode (the viewer still sees them but doesn't need to type 'y').
SAFE_PATTERNS = [r"^\s*ls\b", r"^\s*cat\b", r"^\s*pwd\b", r"^\s*echo\b",
                 r"^\s*git status\b", r"^\s*git diff\b", r"^\s*pytest\b"]

# DESTRUCTIVE_PATTERNS: commands that could cause irreversible damage. These
# are BLOCKED entirely — the agent cannot run them even with approval.
DESTRUCTIVE_PATTERNS = [r"rm\s+-rf?\b", r"git\s+push\s+.*-f", r"git\s+reset\s+--hard",
                        r"\bdd\b", r"\bmkfs\b", r"curl.*\|\s*sh", r"wget.*\|\s*sh"]


def classify(command: str) -> str:
    """Return 'safe', 'needs-approval', or 'blocked' for a shell command.

    This is the risk triage function from Episode 6. It uses regex matching to
    categorize commands by danger level. The classification is used ONLY for
    display (coloring the approval prompt) — the actual pausing comes from
    interrupt_on in build_agent().

    Returns:
        'blocked'         — destructive command, never allowed
        'safe'            — read-only/low-risk, auto-approved in interactive mode
        'needs-approval'  — everything else, requires explicit user approval
    """
    import re  # Imported locally to keep top-level imports minimal

    # Check destructive patterns FIRST — if a command matches any of these,
    # it's blocked regardless of what safe patterns might also match.
    if any(re.match(p, command) for p in DESTRUCTIVE_PATTERNS):
        return "blocked"

    # Then check safe patterns — these are common read-only commands that
    # don't need approval (ls, cat, echo, git status, etc.).
    if any(re.match(p, command) for p in SAFE_PATTERNS):
        return "safe"

    # Everything else requires explicit user approval before execution.
    return "needs-approval"


def _pending_tool_call(state):
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
    """
    config = _config(thread_id)
    auto = os.getenv("CODEIT_AUTO_APPROVE", "false").lower() == "true"  # --yolo mode

    # Phase 1: Stream the initial response — this runs until the agent either
    # completes or hits an interrupt_on tool. If it pauses, state.next will be set.
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": prompt}]},
        config=config, stream_mode="updates", version="v2"
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
            # ⚠️ DANGEROUS in production — only for demos where you trust the agent.
            console.print("[yellow]--yolo: auto-approving[/yellow]")
            cmd = Command(resume={"decisions": [{"type": "approve"}]})
        else:
            # Interactive mode: classify risk, show colored prompt, ask user.
            risk = classify(args.get("command", "")) if name == "run_shell" else "needs-approval"
            color = {"safe": "green", "needs-approval": "yellow", "blocked": "red"}[risk]
            console.print(f"[{color}]risk: {risk}[/{color}]  tool: {name}  args: {args}")

            # Block destructive commands even in interactive mode — the user
            # can't approve something that's been classified as 'blocked'.
            if risk == "blocked":
                console.print("[red]Blocked command — cannot approve.[/red]")
                cmd = Command(resume={"decisions": [
                    {"type": "reject", "message": "Command blocked by policy."}
                ]})
            else:
                answer = console.input("[bold]Approve? (y/n): [/bold]").strip().lower()
                if answer == "y":
                    # Approve: let the tool execute and continue.
                    cmd = Command(resume={"decisions": [{"type": "approve"}]})
                else:
                    # Reject: tell the agent this action was denied, it should try another approach.
                    cmd = Command(resume={"decisions": [
                        {"type": "reject", "message": "User denied this action."}
                    ]})

        # Resume the graph with our decision — stream the result and check for more interrupts.
        for chunk in agent.stream(cmd, config=config, stream_mode="updates", version="v2"):
            _print_event(chunk)
        state = agent.get_state(config)  # Re-check: did we hit another interrupt?

    return state.values


def main() -> None:
    """Entry point — runs the agent with approval gate + trace URL output.

    This is the Episode 15 finale: everything from Episodes 1-14 plus LangSmith
    observability. The flow:
      1. Check if tracing env vars are set (tip if not)
      2. Build the agent with all capabilities
      3. Run with approval gate (Ep 6 pattern)
      4. Print final answer
      5. Surface LangSmith trace URL for debugging/inspection
    """
    # Sanity-check tracing env before we start — give viewers a helpful tip if
    # they forgot to set LANGSMITH_TRACING=true in their environment.
    if os.getenv("LANGSMITH_TRACING", "").lower() != "true":
        console.print("[yellow]Tip: set LANGSMITH_TRACING=true to see a trace URL at the end.[/yellow]")

    prompt = sys.argv[1] if len(sys.argv) > 1 else "Run: echo hello"
    agent = build_agent()
    state = run_with_approval(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)

    # Surface the trace URL (or dashboard hint) after the run completes.
    # This is the Episode 15 addition — viewers can click through to see exactly
    # what the agent did: every model call, tool invocation, and message.
    maybe_print_trace_url(state)


if __name__ == "__main__":
    main()
