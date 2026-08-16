"""
Episode 9 — Context Management: Repo Map & Token Trimming
=========================================================

The agent gains a bird's-eye view of the codebase WITHOUT reading every file.
  1. `build_repo_map(root)` — walks the workspace (hardcoded skip list), uses
     Python's `ast` to extract top-level def/class signatures, returns a compact
     text map. Aider ranks symbols by PageRank — we explicitly DON'T.
  2. `estimate_tokens(text)` — ~4 chars/token heuristic for budgeting.
  3. `trim_history(messages, max_tokens)` — drop oldest turns to fit a cap.

Note: Deep Agents' FilesystemMiddleware already does context engineering
internally. This is a teaching layer for custom control.

Builds on: Episodes 1-8. Requires pip install deepagents langchain-ollama rich.
Run: CODEIT_WORKDIR=./my_project python tutorial.py "Where is X defined? Use build_repo_map first."

Requires: pip install deepagents langchain-ollama rich.
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import ast  # Standard library — parses Python source into AST for signature extraction
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

# ─────────────────────────────────────────────────────────────────────────────
# Constants — hardcoded skip list and limits for the repo map tool.
# We use a simple set instead of parsing .gitignore (avoids adding pathspec dep).
# These values are tuned to keep output compact (~4k tokens) while still useful.
# ─────────────────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "node_modules",  # Noise dirs — skip entirely
    ".pytest_cache",
    ".ruff_cache",
    "workspace",
    ".codeit",
}
SKIP_SUFFIXES = {".pyc", ".pyo"}  # Compiled Python files — no source to show
MAX_FILES = 200  # Cap total files walked (prevents huge repos from blowing context)
MAX_SIGS_PER_FILE = 30  # Max signatures per file before truncation note
MAX_MAP_CHARS = 15_000  # ~4k tokens — keeps the map compact for the model


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
# 1. _signatures — extract top-level def/class signatures from a Python file.
#    Uses the ast module to parse source code into an AST, then walks the body
#    for FunctionDef/AsyncFunctionDef/ClassDef nodes and formats them as strings.
# ─────────────────────────────────────────────────────────────────────────────


def _signatures(path: Path) -> list[str]:
    """Extract top-level function/class signatures from a Python file using ast.

    This is the core of build_repo_map — instead of reading entire files (which
    burns context), we parse each .py file's AST and extract just the signature
    line for each def/class at module level. The model gets a compact overview:
      "Where is X defined?" → scan repo map → read only that specific function.

    Args:
        path: Path to a Python source file.

    Returns: A list of formatted signature strings (e.g., ["def foo(a, b):", ...]).
             Empty list if the file can't be parsed or has no top-level defs/classes.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))  # Parse source into AST
    except Exception:
        return []  # Skip files that can't be read/parsed (syntax errors, encoding issues)

    sigs: list[str] = []
    for node in tree.body:  # Iterate over top-level nodes only (not nested defs/classes)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Extract argument names from the function signature.
            args = [a.arg for a in node.args.args]

            # Distinguish async vs sync functions — important for understanding behavior.
            kind = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            sigs.append(f"{kind} {node.name}({', '.join(args)})")

        elif isinstance(node, ast.ClassDef):
            # For classes, list method names as a compact summary.
            methods = [
                n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            sigs.append(f"class {node.name}" + (f" ({', '.join(methods)})" if methods else ""))

        # Cap signatures per file to keep output compact.
        if len(sigs) >= MAX_SIGS_PER_FILE:
            sigs.append("... [truncated]")
            break

    return sigs


# ─────────────────────────────────────────────────────────────────────────────
# 2. build_repo_map — the custom @tool. Walks the workspace, returns a compact map.
#    For .py files: shows top-level signatures (via _signatures).
#    For other files: shows line count as a quick size indicator.
# ─────────────────────────────────────────────────────────────────────────────


@tool
def build_repo_map(root: str = ".") -> str:
    """Return a compact map of the codebase: file paths + top-level def/class signatures.

    Use this to answer 'where is X defined?' across multiple files without reading them all.
    This saves context — instead of loading every file, you get a bird's-eye view and can
    then read only the specific function you need.

    Args:
        root: Subdirectory to map, relative to workspace (default '.' maps everything).

    Returns: A formatted text string showing each file path with its signatures or line count.
             Truncated at MAX_FILES files and MAX_MAP_CHARS characters for compactness.
    """
    # Resolve the base directory — if root is ".", use workspace root directly.
    base = (_workspace_root() / root).resolve() if root != "." else _workspace_root()

    lines, count = [], 0

    # Walk the directory tree WITHOUT following symlinks (security: prevents loops).
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        # Filter out noise directories IN PLACE — modifying dirnames[:] affects os.walk's traversal.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in sorted(filenames):  # Sort for deterministic output order
            # Skip compiled Python files (.pyc, .pyo) — no source to show.
            if fname.endswith(tuple(SKIP_SUFFIXES)):
                continue

            fpath = Path(dirpath) / fname
            rel = (Path(dirpath) / fname).relative_to(
                _workspace_root()
            )  # Relative path for display

            if fpath.suffix == ".py":
                # For Python files: extract top-level signatures via AST parsing.
                sigs = _signatures(fpath)
                lines.append(f"{rel}:")
                lines.extend(f"  {s}" for s in sigs or ["(no top-level def/class)"])

            else:
                # For non-Python files: show line count as a quick size indicator.
                try:
                    n = sum(1 for _ in fpath.open(encoding="utf-8", errors="ignore"))
                    lines.append(f"{rel}: ({n} lines)")
                except Exception:
                    lines.append(f"{rel}:")  # Can't read — just show the path

            count += 1
            if count >= MAX_FILES:  # Cap total files to prevent context explosion
                lines.append("... [repo map truncated, too many files]")
                break

        if count >= MAX_FILES:
            break

    # Truncate by character count as a final safety net.
    map_text = "\n".join(lines)
    if len(map_text) > MAX_MAP_CHARS:
        map_text = map_text[:MAX_MAP_CHARS] + "\n... [repo map truncated]"

    return map_text or "(empty workspace)"


# ─────────────────────────────────────────────────────────────────────────────
# 3. estimate_tokens + trim_history — teaching-layer context controls.
#    These are NOT tools (not registered with the agent). They're helper functions
#    that demonstrate how to manage token budgets manually, complementing Deep Agents'
#    built-in context engineering in FilesystemMiddleware.
# ─────────────────────────────────────────────────────────────────────────────


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token. Good for budgeting, not billing."""
    return max(1, len(text) // 4)


def trim_history(messages: list, max_tokens: int) -> list:
    """Drop oldest messages until total is under max_tokens. Keeps the newest turn.

    Teaching layer complementing Deep Agents' built-in context engineering.
    This demonstrates the principle of sliding-window context management — older
    turns are dropped to make room for newer ones, but we always keep at least 1 message.

    Args:
        messages: List of chat messages (AIMessage, HumanMessage, etc.).
        max_tokens: Maximum total tokens allowed in the history window.

    Returns: A trimmed list of messages that fits within max_tokens.
    """
    if not messages:
        return []

    def _tok(m) -> int:
        # Estimate tokens for a single message — use content attribute or string repr.
        return estimate_tokens(getattr(m, "content", str(m)) or "")

    kept = list(messages)  # Copy to avoid mutating the original list

    # Drop oldest messages (index 0) until we're under the token cap OR only 1 remains.
    while kept and sum(_tok(m) for m in kept) > max_tokens and len(kept) > 1:
        kept.pop(0)  # Remove the OLDEST message — preserves recent context

    return kept


# ─────────────────────────────────────────────────────────────────────────────
# 4. Build the agent + streaming + approval driver (same shape as Ep 8).
#    The system prompt instructs the model to use build_repo_map for a bird's-eye
#    view before reading specific files, keeping context usage efficient.
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {
    "run_shell": True,
    "write_file": True,
    "edit_file": True,
    "edit_file_safe": True,
    "delete": True,
}


def build_agent(workdir: str | None = None):
    """Build the Deep Agent with repo mapping capability.

    This extends Ep 8's agent by adding build_repo_map as a custom tool and
    updating the system prompt to instruct the model on when to use it for context efficiency.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    # Create the workspace directory if it doesn't exist yet — ensures sandbox is ready
    root.mkdir(parents=True, exist_ok=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[build_repo_map],  # Custom tool: compact codebase map via AST signatures
        system_prompt=(
            "You are CodeIt, a coding agent. Use build_repo_map for a bird's-eye "
            "view of the codebase, then read_file only the files you need."
        ),
        backend=FilesystemBackend(  # Built-in filesystem tools with sandbox ON
            root_dir=str(root),  # Confine all file ops to this directory
            virtual_mode=True,  # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        interrupt_on=INTERRUPT_ON,  # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),  # REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Streaming + approval driver (same shape as Eps 6-8).
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


def main() -> None:
    """Entry point — build the agent with repo mapping and run it.

    The demo prompt asks the agent to find a file using build_repo_map, demonstrating
    how context-efficient exploration works without reading every file in the project.
    """
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Where is the main file? Use build_repo_map."

    agent = build_agent()
    state = run_with_approval(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


if __name__ == "__main__":
    main()
