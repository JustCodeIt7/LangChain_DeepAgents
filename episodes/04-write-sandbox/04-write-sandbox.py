"""
Episode 4 — Writing Code: `write_file` + the Workspace Sandbox
==============================================================

The shortest episode. `write_file` is already provided by FilesystemBackend
— we don't write any new tool code. The work here is:

  1. Reinforce the sandbox story (virtual_mode=True earns its keep).
  2. Add `resolve_in_workspace(path) -> Path` — a helper that custom tools
     in later episodes (shell, edit wrapper, repo map) will use to share
     the backend's sandbox discipline.

The viewer asks the agent to write a file; the agent uses the built-in
`write_file`; the viewer opens the file on disk — real code, written by
the agent.

Builds on: Episode 3 (FilesystemBackend, custom tools).

Run:
    CODEIT_WORKDIR=./workspace python tutorial.py \
        "Create main.py with a FastAPI app: GET /hello returns {'msg':'hello'}."

Requires:
    pip install deepagents langchain-ollama rich
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import os  # Environment variable access for provider/model/workdir config
import sys  # Command-line argument parsing (sys.argv[1])
from pathlib import Path  # Object-oriented filesystem paths with .resolve() and .relative_to()

# Deep Agents harness — the core framework that compiles a LangGraph agent.
from deepagents import create_deep_agent  # Creates compiled agent graph
from deepagents.backends import FilesystemBackend  # Built-in fs tools: ls/read/write/edit/glob/grep

# LangChain — provider-agnostic LLM integration and tool definitions.
from langchain.chat_models import init_chat_model  # One call, any provider

# LangChain Core — type hints for model and message objects.
from langchain_core.language_models import BaseChatModel  # Return type of get_model()
from langchain_core.messages import AIMessage  # Message type with tool_calls

# ─────────────────────────────────────────────────────────────────────────────
# InMemorySaver vs MemorySaver: Deep Agents v0.6.x uses InMemorySaver (not
# MemorySaver). Both are in-process checkpointers, but the class name differs
# across versions — check your installed version's docs if this errors.
# ─────────────────────────────────────────────────────────────────────────────
from langgraph.checkpoint.memory import InMemorySaver  # In-process state persistence

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
# 1. resolve_in_workspace — share the sandbox discipline across custom tools.
#    Mirrors what FilesystemBackend(virtual_mode=True) does internally, but
#    for OUR tools (run_shell in Ep 5, edit_file_safe in Ep 8, etc.).
# ─────────────────────────────────────────────────────────────────────────────

class PathEscapeError(PermissionError):
    """Raised when a resolved path leaves the workspace sandbox.

    This is a custom exception that subclasses PermissionError so callers can
    catch it specifically or as part of broader permission error handling.
    The virtual_mode=True in FilesystemBackend does this check internally;
    we replicate it here for our own tools that need to write files safely.
    """


def workspace_root() -> Path:
    """Resolve the sandbox root directory from CODEIT_WORKDIR env var.

    Returns an absolute, resolved Path so all file operations are confined
    to this directory tree. The .resolve() call normalizes any ../ or ./ in
    the path and resolves symlinks — critical for security checks downstream.
    """
    return Path(os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()


def resolve_in_workspace(path: str | Path) -> Path:
    """Resolve `path` relative to CODEIT_WORKDIR, refusing to escape.

    This is the core sandbox enforcement function — it prevents path traversal
    attacks where a malicious or buggy tool might try to write outside the workspace.

    How it works:
      1. Get the absolute root of the workspace (e.g., /home/user/workspace)
      2. Join the requested path under that root and resolve all symlinks/../
      3. Check if the resolved target is still inside the root using .relative_to()
         - If it IS inside: returns the safe absolute Path
         - If it ESCAPED (e.g., ../../etc/passwd): raises PathEscapeError

    Blocks `../`, `~`, and absolute paths outside the workspace root.
    Follows symlinks via .resolve(), then checks the result is still inside.

    Args:
        path: A relative or absolute path string, or a Path object.

    Returns:
        The resolved absolute Path if it's within the workspace.

    Raises:
        PathEscapeError: If the resolved path escapes the workspace boundary.
    """
    root = workspace_root()  # Get the sandbox root as an absolute Path
    target = (root / path).resolve()  # Join and resolve — follows symlinks, normalizes ../

    try:
        # .relative_to() raises ValueError if `target` is NOT under `root`.
        # This is our security check: if the resolved path escapes the sandbox,
        # this call fails and we raise PathEscapeError instead.
        target.relative_to(root)
    except ValueError:
        # The path escaped the workspace — refuse to proceed.
        # noqa: B904 suppresses ruff's warning about not using `raise ... from`
        # because we're intentionally converting ValueError → PathEscapeError here.
        raise PathEscapeError(  # noqa: B904
            f"Path {path!r} resolves outside the workspace ({root}). Refusing."
        )

    return target


# ─────────────────────────────────────────────────────────────────────────────
# 2. Build the agent — same as Ep 3. write_file is already exposed by the
#    backend; we don't add it ourselves. No new tools this episode.
# ─────────────────────────────────────────────────────────────────────────────

def build_agent(workdir: str | None = None):
    """Build a Deep Agents graph with filesystem sandbox enabled.

    The agent gets two categories of tools:
      - Built-in filesystem tools (ls, read_file, write_file, edit_file, glob, grep)
        provided automatically by FilesystemBackend(virtual_mode=True).
      - No custom tools this episode — we're reinforcing the sandbox story.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream.
    """
    # Resolve and create the workspace directory — ensures sandbox exists before agent runs.
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    root.mkdir(parents=True, exist_ok=True)

    # FilesystemBackend provides built-in tools with path traversal protection.
    backend = FilesystemBackend(root_dir=str(root), virtual_mode=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[],  # write_file/read_file/ls/etc. come from the backend — no custom tools needed
        system_prompt=(
            "You are CodeIt, a coding agent. Use write_file to CREATE new files."
            " Use edit_file for changes to existing files."
            " Keep files inside the workspace."
        ),
        backend=backend,  # Built-in filesystem tools with sandbox ON (virtual_mode=True)
        checkpointer=InMemorySaver(),  # In-process state persistence — needed for streaming resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Streaming driver (same shape as Eps 2-3).
#    Dual-mode: 'updates' for live rendering, final state capture via get_state().
# ─────────────────────────────────────────────────────────────────────────────

def _config(thread_id: str) -> dict:
    """Build the LangGraph config dict with thread ID + recursion limit.

    - configurable.thread_id: groups related turns into a conversation thread
      (required for InMemorySaver to persist state across resume).
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

    for _node, state in chunk.get("data", {}).items():  # Iterate over node states in this update
        if not isinstance(state, dict):  # Some nodes aren't message-based — skip them
            continue
        for msg in state.get("messages", []):  # Each node may have multiple messages
            if isinstance(msg, AIMessage) and msg.tool_calls:  # Model decided to call a tool
                for tc in msg.tool_calls:
                    console.print(f"[cyan]tool call:[/cyan] {tc['name']}({tc['args']})")
            elif isinstance(msg, AIMessage) and msg.content:  # Plain text response from the model
                console.print(f"[green]assistant:[/green] {msg.content}")


def run(agent, prompt: str, thread_id: str = "default") -> dict:
    """Stream the agent's response live to the console.

    The flow:
      1. Stream with stream_mode='updates' — each chunk is a node state snapshot.
      2. _print_event renders tool calls and assistant messages as they happen.
      3. After streaming completes (or errors), return final state values.

    Args:
        agent: The compiled Deep Agents graph from build_agent().
        prompt: Initial task for the agent (e.g., "Create main.py").
        thread_id: Conversation thread ID — must match across stream/resume calls.

    Returns: Final agent state dict with messages and values.
    """
    config = _config(thread_id)

    try:
        # Stream in 'updates' mode — fires on each node execution, giving us live rendering.
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": prompt}]},
            config=config, stream_mode="updates", version="v2",
        ):
            _print_event(chunk)
    except Exception as e:
        # Catch broad exceptions to handle GraphRecursionError and model errors gracefully.
        console.print(f"[red]error:[/red] {type(e).__name__}: {e}")

    return agent.get_state(config).values


def main() -> None:
    """Entry point — build the sandboxed agent and write a file via the backend.

    The demo prompt asks the agent to create a FastAPI app in main.py, demonstrating
    how FilesystemBackend's built-in write_file tool safely writes files within
    the workspace sandbox (virtual_mode=True prevents path traversal).
    """
    # Read the task from CLI args; default creates a simple FastAPI file.
    prompt = sys.argv[1] if len(sys.argv) > 1 else (
        "Create main.py with a FastAPI app: GET /hello returns {'msg':'hello'}."
    )

    agent = build_agent()
    state = run(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)

    # Show that the file actually landed on disk — proving the agent wrote real code.
    out = workspace_root() / "main.py"
    if out.exists():
        print(f"\n(wrote {out} — {out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
