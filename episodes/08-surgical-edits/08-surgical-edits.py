"""
Episode 8 — Surgical Edits: `edit_file` + the Fuzzy Fallback Wrapper
====================================================================

The agent graduates from whole-file rewrites to SEARCH-REPLACE edits — the
format used by Aider, Codex, and Cline. We add a teaching wrapper,
`edit_file_safe(path, search, replace)`: exact match first, difflib fuzzy
match (>=90%) on a miss, unified diff on total failure so the model
self-corrects. Goes through the Ep 6 approval gate.

Builds on: Episodes 1-7.

Run:
    CODEIT_WORKDIR=./workspace python tutorial.py \
        "In big.py, change line 50 to say 'EDITED' instead of 'some content'. Use edit_file_safe."

Requires: pip install deepagents langchain-ollama rich.
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import difflib  # Standard library — SequenceMatcher for fuzzy matching + unified_diff for errors
import os  # Environment variable access for provider/model/workdir config
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


def _resolve_in_workspace(path: str) -> Path:
    """Resolve `path` against the workspace, refusing to escape (Ep 4 helper).

    This is the same sandbox discipline from Episode 4 — we share it across custom tools.
    Blocks ../, ~/, and absolute paths outside the workspace root by resolving
    the path then checking it's still relative_to the root via .relative_to().

    Args:
        path: A file path (may be relative or contain ../ sequences).

    Returns: The resolved Path object if inside the workspace.

    Raises: PermissionError if the path escapes the workspace sandbox.
    """
    root = _workspace_root()

    # Strip leading slashes so '/big.py' is treated as 'big.py' relative to root.
    # This prevents absolute paths from being interpreted as system-absolute.
    clean = path.lstrip("/")

    target = (root / clean).resolve()  # Resolve follows symlinks and normalizes ../ sequences

    try:
        target.relative_to(root)  # Raises ValueError if target is outside root
    except ValueError:
        raise PermissionError(f"Path {path!r} escapes workspace ({root}).") from None

    return target


# ─────────────────────────────────────────────────────────────────────────────
# 1. _fuzzy_find — O(n*m) scan with difflib. Cap file size at 50k chars.
#    When the model's memory of a code snippet is slightly off (whitespace, typos),
#    exact match fails but fuzzy matching can still find it. This prevents the agent
#    from getting stuck on minor mismatches that would otherwise require re-reading.
# ─────────────────────────────────────────────────────────────────────────────


def _fuzzy_find(text: str, search: str, threshold: float = 0.90):
    """Find the substring of `text` most similar to `search`, above `threshold`.

    Uses difflib.SequenceMatcher.ratio() — a measure of sequence similarity from
    0.0 (completely different) to 1.0 (identical). We slide a window of len(search)
    across text and find the position with the highest ratio.

    This is an O(n*m) scan where n=len(text), m=len(search). For large files we
    cap at 50k chars to prevent slow performance — most code snippets are short.

    Args:
        text: The full file content to search within.
        search: The snippet the model thinks is in the file (may have minor differences).
        threshold: Minimum similarity ratio required for a match (default 0.90 = 90%).

    Returns: A tuple of (matched_substring, score) if above threshold, else (None, best_score).
             The caller can use the returned None to trigger the diff fallback path.
    """
    # Guard against empty search or excessively large files — prevents slow scans.
    if not search or len(text) > 50_000:
        return None, 0.0

    best, best_score = None, 0.0
    n = len(search)

    # Slide a window of size n across the text and compute similarity at each position.
    for i in range(0, max(0, len(text) - n + 1)):
        score = difflib.SequenceMatcher(None, search, text[i : i + n]).ratio()
        if score > best_score:
            best, best_score = text[i : i + n], score

            # Early exit on perfect match — no need to keep scanning.
            if best_score == 1.0:
                break

    # Return the best match only if it meets the threshold; otherwise return None
    # so the caller can fall through to the unified diff error path.
    return (best, best_score) if best_score >= threshold else (None, best_score)


# ─────────────────────────────────────────────────────────────────────────────
# 2. edit_file_safe — the custom @tool. Docstring explains the three outcomes
#    so the model learns the contract: exact / fuzzy / fail-with-diff.
#    This is a teaching wrapper around search-replace that helps the model self-correct.
# ─────────────────────────────────────────────────────────────────────────────


@tool
def edit_file_safe(path: str, search: str, replace: str) -> str:
    """Edit a file by replacing `search` text with `replace` text (first occurrence).

    For targeted changes to existing files — never rewrite a whole file. This is the
    search-replace format used by Aider, Codex, and Cline. The docstring explains three outcomes:

    Args:
        path: File relative to workspace (e.g., 'main.py').
        search: Exact text to find; include enough context to be unique.
        replace: New text to substitute in place of the matched search string.

    Returns one of three outcomes:
      1. EXACT MATCH — "Applied exact match edit" — search found verbatim, replaced.
      2. FUZZY MATCH (>=90% similar) — applied with a note to review the result.
         This handles minor whitespace/typo differences in the model's memory of the code.
      3. NO MATCH — returns a unified diff showing current state vs proposed edit,
         so the model can see what went wrong and retry with corrected search text.

    On any outcome: only the FIRST occurrence is replaced (text.replace(search, replace, 1)).
    """
    try:
        # Read the file content through our sandbox resolver — blocks path traversal.
        text = _resolve_in_workspace(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Error: {path} not found in workspace."
    except Exception as e:
        return f"Error reading {path}: {type(e).__name__}: {e}"

    if search not in text:
        # Exact match failed — try fuzzy matching to handle minor differences.
        best, score = _fuzzy_find(text, search, threshold=0.90)

        if best is not None:
            # Fuzzy match found (>= 90% similar) — apply the edit with a warning note.
            new_text = text.replace(best, replace, 1)  # Replace first occurrence of fuzzy match
            _resolve_in_workspace(path).write_text(new_text, encoding="utf-8")
            return f"Applied fuzzy match (similarity {score:.2f}). Review the result."

        # No match at all — generate a unified diff so the model can see what went wrong.
        # The diff shows: current file content vs proposed edit that was NOT applied.
        # This teaches the model to re-read the file and retry with corrected search text.
        diff = difflib.unified_diff(
            text.splitlines(keepends=True),  # Current file lines (fromfile)
            (text + "\n# --- proposed edit did not apply ---\n").splitlines(keepends=True),
            fromfile=f"{path} (current)",
            tofile=f"{path} (NOT applied)",
            n=3,
        )

        return (
            f"Could not find the search text in {path} "
            f"(best similarity {score:.2f}, needed >=0.90). NOT modified.\n\n" + "".join(diff)
        )

    # Exact match found — apply the edit directly, replacing only the first occurrence.
    new_text = text.replace(search, replace, 1)  # First occurrence only — surgical precision
    _resolve_in_workspace(path).write_text(new_text, encoding="utf-8")
    return f"Applied exact match edit to {path}."


# ─────────────────────────────────────────────────────────────────────────────
# 3. Build the agent — gate edit_file_safe too (it mutates files).
#    The system prompt instructs the model on when and how to use this tool,
#    including what to do when a search misses (re-read and retry).
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {
    "run_shell": True,
    "write_file": True,
    "edit_file": True,
    "edit_file_safe": True,
    "delete": True,
}


def build_agent(workdir: str | None = None):
    """Build the Deep Agent with surgical edit capability.

    This extends Ep 7's agent by adding edit_file_safe as a custom tool and
    updating the system prompt to instruct the model on search-replace editing.

    The key insight: edit_file_safe goes through the approval gate (interrupt_on)
    because it mutates files — we want human oversight before any file modification.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    # Create the workspace directory if it doesn't exist yet — ensures sandbox is ready
    root.mkdir(parents=True, exist_ok=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[edit_file_safe],  # Custom tool: surgical search-replace edits with fuzzy fallback
        system_prompt=(
            "You are CodeIt, a coding agent. Use edit_file_safe for targeted "
            "changes to existing files. If a search misses, re-read and retry."
        ),
        backend=FilesystemBackend(  # Built-in filesystem tools with sandbox ON
            root_dir=str(root),  # Confine all file ops to this directory
            virtual_mode=True,  # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        interrupt_on=INTERRUPT_ON,  # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),  # REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Streaming + approval driver (same shape as Eps 6-7).
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
    """invoke → if paused, ask → resume → repeat.

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


def main() -> None:
    """Entry point — build the agent with surgical edit capability and run it.

    The demo prompt asks the agent to make a targeted change using edit_file_safe,
    demonstrating how search-replace edits work with the fuzzy fallback for minor mismatches.
    """
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "In big.py, change line 50 to 'EDITED'. Use edit_file_safe."
    )

    agent = build_agent()
    state = run_with_approval(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


if __name__ == "__main__":
    main()
