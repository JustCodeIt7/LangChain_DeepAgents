"""
Episode 3 — Giving Your Agent Hands: Filesystem Tools
====================================================

We attach a `FilesystemBackend(root_dir=..., virtual_mode=True)` and the
built-in read-only filesystem tools — `ls`, `read_file`, `glob`, `grep` —
appear automatically. Zero hand-written tool code from us for those four.

We DO add one custom `@tool`, `read_summary`, that wraps the idea of
read_file with line truncation. It shows how to register a custom tool
alongside the built-ins.

SECURITY: `virtual_mode=True` is the sandbox. The default `virtual_mode=False`
provides NO security even with `root_dir` set. Always pass `virtual_mode=True`.

Builds on: Episodes 1-2 (get_model, build_agent, streaming).

Run:
    # Point CODEIT_WORKDIR at any small project folder, then:
    CODEIT_WORKDIR=./my_project python tutorial.py "What's in this project?"

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
from pathlib import Path  # Object-oriented filesystem paths with .resolve()

# Deep Agents harness — the core framework that compiles a LangGraph agent.
from deepagents import create_deep_agent  # Creates compiled agent graph

# FilesystemBackend is the Deep Agents backend that provides ls/read_file/
# write_file/edit_file/glob/grep automatically when attached.
# Verified: `from deepagents.backends import FilesystemBackend` (deep-agents-core skill).
from deepagents.backends import FilesystemBackend

# LangChain — provider-agnostic LLM integration and tool definitions.
from langchain.chat_models import init_chat_model  # One call, any provider
from langchain.tools import tool  # Decorator → LLM-callable Tool

# LangChain Core — type hints for model and message objects.
from langchain_core.language_models import BaseChatModel  # Return type of get_model()
from langchain_core.messages import AIMessage  # Message type with tool_calls

# ─────────────────────────────────────────────────────────────────────────────
# MemorySaver vs InMemorySaver: Deep Agents v0.6.x uses MemorySaver (not
# InMemorySaver). Both are in-process checkpointers, but the class name differs
# across versions — check your installed version's docs if this errors.
# ─────────────────────────────────────────────────────────────────────────────
from langgraph.checkpoint.memory import MemorySaver  # In-process state persistence

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
# 1. A custom tool — `read_summary`. Wraps read_file with truncation policy.
#    The docstring is FOR THE MODEL: "Use this when you want a quick overview…"
#
#    WHY CUSTOM TOOLS? FilesystemBackend provides ls/read_file/write_file/etc.,
#    but sometimes we need domain-specific behavior (truncation, formatting).
#    Custom @tool functions let us add that while still using the backend's tools.
# ─────────────────────────────────────────────────────────────────────────────

@tool
def read_summary(path: str) -> str:
    """Read a file and return its first 50 lines plus a truncation note.

    Use this when you want a quick overview of a file without reading the whole thing.
    Argument: path relative to the workspace root (e.g. 'main.py' or 'src/app.py').

    This demonstrates how custom tools complement FilesystemBackend's built-in read_file:
      - We add truncation so very large files don't fill the context window.
      - The docstring is a PROMPT for the model — it tells the LLM when to use this tool.
      - Errors are returned as strings (not raised) so the agent can self-correct.
    """
    # Resolve the workspace root from CODEIT_WORKDIR env var, defaulting to ./workspace.
    root = Path(os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()

    try:
        text = (root / path).read_text(encoding="utf-8")  # Read file content as UTF-8 string
    except FileNotFoundError:
        return f"Error: {path} not found in workspace."  # Return error string — model can adapt
    except Exception as e:
        return f"Error reading {path}: {type(e).__name__}: {e}"

    lines = text.splitlines()  # Split into lines for truncation logic

    if len(lines) <= 50:
        return text  # Small file — return everything, no need to truncate

    # Large file — return first 50 lines with a note about remaining content.
    # This prevents huge files from consuming the entire context window.
    return "\n".join(lines[:50]) + f"\n... [truncated, {len(lines) - 50} more lines]"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Build the agent — attach a FilesystemBackend with the sandbox ON.
#    This is where we wire everything together: model + tools + backend + checkpointer.
# ─────────────────────────────────────────────────────────────────────────────

def build_agent(workdir: str | None = None):
    """Build a Deep Agents graph with filesystem sandbox enabled.

    The agent gets two categories of tools:
      - Built-in filesystem tools (ls, read_file, glob, grep) provided automatically
        by FilesystemBackend(virtual_mode=True). These are READ-ONLY in this episode.
      - Our custom read_summary tool for truncated file previews.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream.
    """
    # Resolve and create the workspace directory — ensures sandbox exists before agent runs.
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    root.mkdir(parents=True, exist_ok=True)

    # virtual_mode=True blocks ../, ~, and absolute paths outside root.
    # NEVER set virtual_mode=False with a real root_dir. It is insecure by default.
    backend = FilesystemBackend(root_dir=str(root), virtual_mode=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[read_summary],  # our custom tool alongside the built-ins
        system_prompt="You are CodeIt, a helpful coding assistant. Explore the workspace.",
        backend=backend,  # ← ls/read_file/glob/grep appear automatically — no registration needed!
        checkpointer=MemorySaver(),  # In-process state persistence — needed for streaming resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Streaming driver (same shape as Ep 2).
#    Dual-mode: 'updates' for live rendering, final state capture via get_state().
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
        prompt: Initial task for the agent (e.g., "What's in this project?").
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
    """Entry point — build the sandboxed agent and explore a project directory.

    The demo prompt asks the agent to list files in the workspace, demonstrating how
    FilesystemBackend's built-in ls tool safely reads directory contents within
    the sandbox (virtual_mode=True prevents path traversal).
    """
    # Read the task from CLI args; default explores the current workspace.
    prompt = sys.argv[1] if len(sys.argv) > 1 else "What files are in this project?"

    agent = build_agent()
    state = run(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


if __name__ == "__main__":
    main()
