"""
Episode 11 — Error Recovery: Self-Healing Loops
================================================

The "wow" episode. The agent writes code, runs it, reads the failure, and
fixes it — autonomously, up to a retry cap. Two pieces:
  1. `run_tests(path)` — a custom @tool that runs `pytest` in the workspace,
     captures failures, returns a readable string.
  2. `run_with_recovery(agent, prompt, thread_id, max_retries)` — a plain
     Python loop AROUND the Deep Agents graph. After the agent finishes, if
     run_tests reported failures, re-invoke the agent with the failure output
     appended as a user message; cap retries. Implemented AROUND the graph,
     not as a new graph node — we don't fight the framework.

⚠️ Assumption: failure-detection heuristic looks for "[exit 1]" + "FAILED" or
"Error" in a tool message. Tighten if you see false recoveries in the demo.
⚠️ Model size: recovery is unreliable on small local models. Use 32b or OpenAI.

Builds on: Episodes 1-10. Requires pip install deepagents langchain-ollama rich pytest.
Run: CODEIT_WORKDIR=./my_project python tutorial.py \
     "Run the tests. If they fail, read the failure and fix the code. Then run tests again."

Requires: pip install deepagents langchain-ollama rich pytest.
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import os  # Environment variable access for provider/model/workdir config
import subprocess  # Running shell commands in run_shell and run_tests tools
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

# LangGraph — state persistence and interrupt/resume primitives.
from langgraph.checkpoint.memory import MemorySaver  # REQUIRED for interrupts (Ep 6)
from langgraph.types import Command  # Resume: Command(resume={"decisions":[...]})

# Rich — colored, live terminal output for the streaming view.
from rich.console import Console  # Renders [color] tags + handles input()


console = Console()  # Single shared console instance; reused across all print calls in this script

# MAX_OUTPUT_CHARS caps how much text a tool returns to the model. Failure output
# can be very long (tracebacks, full test dumps). We truncate at ~4k tokens so we
# don't blow the context window on irrelevant noise — the key error is usually near the top.
MAX_OUTPUT_CHARS = 15_000


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


def _workspace_root() -> Path:
    """Resolve CODEIT_WORKDIR to an absolute path.

    This is the sandbox root — all file operations are confined here by
    FilesystemBackend(virtual_mode=True). The .resolve() call follows symlinks
    and normalizes ../ sequences so we can do a clean relative_to check later.
    """
    return Path(os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()


# ─────────────────────────────────────────────────────────────────────────────
# 1. run_tests — a custom @tool. Thin: subprocess + pytest -q --tb=short.
#    Non-zero exit returns a STRING (not an exception) so the model reads
#    "[exit 1]" and self-corrects. The docstring primes the recovery loop.
# ─────────────────────────────────────────────────────────────────────────────


@tool
def run_tests(path: str = ".") -> str:
    """Run pytest in the workspace and return pass/fail summary + failures.

    Use this after editing code that has tests, to check your work. If tests fail,
    read the failure output and fix the code, then run_tests again.

    Args:
        path: Test path relative to workspace (default '.' runs all tests).

    Returns a formatted string with exit code, stdout, stderr, and truncation note.
    Non-zero exits are returned as strings (not exceptions) so the model can read
    "[exit 1]" and self-correct in its next turn — this is what enables the recovery loop.
    """
    try:
        # Run pytest with quiet output (-q), short tracebacks (--tb=short), no header.
        # We use a list (not shell=True) for safety — no injection risk since we're
        # passing args directly, not through a shell interpreter.
        proc = subprocess.run(
            ["pytest", path, "-q", "--tb=short", "--no-header"],
            cwd=str(_workspace_root()),  # Confine to workspace sandbox
            capture_output=True,  # Capture stdout + stderr separately
            text=True,  # Return strings, not bytes
            timeout=180,  # Kill after 3 minutes — tests can take a while
        )
    except subprocess.TimeoutExpired:
        return "Error: pytest timed out after 180s."
    except FileNotFoundError:
        return "Error: pytest not installed. Run: pip install pytest"
    except Exception as e:
        return f"Error launching pytest: {type(e).__name__}: {e}"

    # Format output with exit code — the "[exit N]" pattern is what our failure
    # detector (_detect_test_failure) looks for to trigger self-healing recovery.
    combined = f"$ pytest {path}\n[exit {proc.returncode}]\n{proc.stdout or ''}"

    if proc.stderr:  # Append stderr separately so it's clearly delineated
        combined += f"\n--- stderr ---\n{proc.stderr}\n"

    # Truncate output to MAX_OUTPUT_CHARS — failure tracebacks can be very long.
    # We keep the beginning (where the error usually is) and note what was cut.
    if len(combined) > MAX_OUTPUT_CHARS:
        combined = (
            combined[:MAX_OUTPUT_CHARS]
            + f"\n... [truncated, {len(combined) - MAX_OUTPUT_CHARS} more chars]"
        )

    return combined


# ─────────────────────────────────────────────────────────────────────────────
# 2. Build the agent — register run_tests alongside built-ins.
#    The system prompt primes the model to use run_tests after editing code and
#    self-correct if tests fail — this is what makes recovery possible.
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {
    "run_shell": True,
    "write_file": True,
    "edit_file": True,
    "edit_file_safe": True,
    "delete": True,
}


def build_agent(workdir: str | None = None):
    """Build the Deep Agent with test-running capability.

    This extends Ep 10's agent by adding run_tests as a custom tool and updating
    the system prompt to instruct the model on how to use it for self-correction.

    The key insight: we DON'T implement recovery inside the graph (as a node).
    Instead, we wrap the entire graph invocation in a Python loop that detects
    failures and re-invokes with additional context. This is simpler and more
    flexible than fighting the framework's internals.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    # Create the workspace directory if it doesn't exist yet — ensures sandbox is ready
    root.mkdir(parents=True, exist_ok=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[run_tests],  # Custom tool: run pytest in the workspace
        system_prompt=(
            "You are CodeIt, a coding agent. After editing code with tests, call "
            "run_tests. If tests fail, read the failure, fix the code, then run_tests again."
        ),
        backend=FilesystemBackend(  # Built-in filesystem tools with sandbox ON
            root_dir=str(root),  # Confine all file ops to this directory
            virtual_mode=True,  # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        interrupt_on=INTERRUPT_ON,  # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),  # REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Streaming + approval driver (same shape as Eps 6-10).
#    This section handles live rendering of agent events and the human-in-the-loop
#    approval gate when interrupt_on tools are called.
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
        if not pending:
            break

        name, args = pending

        if auto:
            # --yolo mode: skip the prompt and approve everything automatically.
            console.print("[yellow]--yolo: auto-approving[/yellow]")
            cmd = Command(resume={"decisions": [{"type": "approve"}]})
        else:
            # Interactive mode: show what's about to happen, ask user for approval.
            console.print(f"tool: {name}  args: {args}")
            answer = console.input("[bold]Approve? (y/n): [/bold]").strip().lower()
            cmd = (
                Command(resume={"decisions": [{"type": "approve"}]})
                if answer == "y"
                else Command(resume={"decisions": [{"type": "reject", "message": "No."}]})
            )

        # Resume the graph with our decision — stream the result and check for more interrupts.
        for chunk in agent.stream(cmd, config=config, stream_mode="updates", version="v2"):
            _print_event(chunk)
        state = agent.get_state(config)  # Re-check: did we hit another interrupt?

    return state.values


# ─────────────────────────────────────────────────────────────────────────────
# 4. _detect_test_failure — heuristic scan of final state's tool messages.
#    Only checks the LAST run_tests result, not all tool messages, to avoid false
#    positives from earlier failures in the conversation history.
# ─────────────────────────────────────────────────────────────────────────────


def _detect_test_failure(state: dict) -> str | None:
    """Inspect agent's final state for a run_tests result that reported failure.

    The heuristic scans messages in REVERSE order (newest first). It looks for
    the most recent tool message containing "[exit 1]" + "FAILED" or "Error".
    If it finds an exit-0 result before any failure, tests passed — return None.

    ⚠️ This is a HEURISTIC, not perfect. False positives can occur if:
      - A previous test run failed but the agent fixed and re-ran successfully
        (we stop at "[exit 0]" to handle this case)
      - The model's output format differs from our expected pattern

    Args:
        state: The final agent state dict containing "messages" list.

    Returns: The failure content string if a test failure is detected, else None.
    """
    if not state:
        return None

    # Scan messages in reverse — we want the MOST RECENT tool result first.
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", "") != "tool":  # Only inspect tool result messages
            continue

        content = getattr(msg, "content", "") or ""

        # Check for failure pattern: non-zero exit + error indicators.
        # The "[exit N]" format is what run_tests returns — we look for [exit 1]
        # combined with FAILED (pytest's failure marker) or Error (general errors).
        if "[exit 1]" in content and ("FAILED" in content or "Error" in content):
            return content

        # If we hit any tool result that succeeded ([exit 0]), tests passed.
        # Stop scanning — don't look at older failures from previous attempts.
        if "[exit 0]" in content:
            return None

        # First tool message found, not a failure — no test was run or it's unrelated.
        return None

    return None


# ─────────────────────────────────────────────────────────────────────────────
# 5. run_with_recovery — plain Python loop AROUND the graph (not a node).
#    This is the "wow" factor: after the agent finishes, if tests failed, we
#    re-invoke with the failure output appended as a user message. The SAME
#    thread_id persists history so the model sees what it already did.
# ─────────────────────────────────────────────────────────────────────────────


def run_with_recovery(agent, prompt: str, thread_id: str = "default", max_retries: int = 3) -> dict:
    """Run agent; if run_tests reports failures, re-invoke with the failure appended.

    This is a PLAIN PYTHON LOOP around the Deep Agents graph — NOT a new graph node.
    We don't fight the framework's internals; instead we wrap invoke() in a loop
    that detects failures and feeds them back as user messages.

    The recovery flow:
      1. Run the agent with the original prompt (via run_with_approval)
      2. Check if tests failed using _detect_test_failure
      3. If failure detected, append it as a USER message and re-invoke
         — same thread_id so history persists (code written, tests run)
      4. Repeat up to max_retries times

    ⚠️ Model size: recovery is unreliable on small local models. Use 32b or OpenAI.
       The model needs enough reasoning capacity to read a traceback and fix the bug.

    Args:
        agent: The compiled Deep Agents graph from build_agent()
        prompt: Initial task for the agent (e.g., "fix the failing test")
        thread_id: Conversation thread ID — SAME across retries so history persists
        max_retries: Maximum number of recovery attempts before giving up

    Returns: Final agent state dict with messages and values.
    """
    # Phase 1: Run the agent on the original prompt with approval gate enabled.
    state = run_with_approval(agent, prompt, thread_id)

    # Phase 2: Check for test failures and retry if needed (up to max_retries).
    for attempt in range(max_retries):
        failure = _detect_test_failure(state)
        if not failure:
            return state  # No failure detected — we're done!

        # Failure detected — print a warning and prepare the follow-up message.
        console.print(
            f"[yellow]Test failure detected (attempt {attempt + 1}/{max_retries}). "
            f"Re-invoking...[/yellow]"
        )

        # The follow-up is a USER message so the model treats it as new input,
        # not as part of its own previous reasoning. We include the full failure
        # output so the model can read the traceback and understand what went wrong.
        followup = (
            f"The tests failed. Here is the output:\n\n{failure}\n\n"
            f"Read the failure, fix the code, then run_tests again."
        )

        # Re-invoke with the SAME thread_id — this preserves conversation history
        # so the model sees what it already wrote and can build on that context.
        state = run_with_approval(agent, followup, thread_id)

    # Recovery cap reached — we tried max_retries times but tests still fail.
    console.print(f"[red]Recovery cap reached ({max_retries} retries). Stopping.[/red]")
    return state


def main() -> None:
    """Entry point — build the agent and run with self-healing recovery loop.

    The demo prompt asks the agent to fix failing tests, triggering the full
    recovery cycle: write code → run tests → detect failure → re-invoke with
    failure context → repeat until fixed or retries exhausted.

    CODEIT_MAX_RETRIES env var controls the retry cap (default 3).
    """
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Run the tests. If they fail, read the failure and fix the code. Then run tests again."
    )

    agent = build_agent()

    # Run with recovery — max_retries comes from env var (default 3).
    state = run_with_recovery(agent, prompt, max_retries=int(os.getenv("CODEIT_MAX_RETRIES", "3")))

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


if __name__ == "__main__":
    main()
