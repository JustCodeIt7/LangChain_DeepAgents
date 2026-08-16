"""
Episode 5 — Running Commands: the Shell Tool (and why it's dangerous)
=====================================================================

The agent gains the ability to run shell commands. There is NO built-in
`run_shell` in FilesystemBackend, so we write a custom `@tool` that:

  - Runs the command with cwd = CODEIT_WORKDIR (via workspace_root()).
  - Captures stdout, stderr, and exit code.
  - Truncates long output so we don't blow the context window.
  - Returns a single readable string to the model.

NO gating this episode. The agent CAN `rm -rf` the workspace. That's the
cliffhanger — end the episode pointing at Episode 6 (the approval gate).

Be honest on camera: run_shell confines CWD, not the process. `rm -rf /`
would still try to delete the system if the user has permission. NEVER run
unsandboxed on a real repo.

Builds on: Episodes 1-4 (model, agent, FilesystemBackend, resolve_in_workspace).

Run:
    CODEIT_WORKDIR=./my_project python tutorial.py \
        "Install fastapi and uvicorn with pip, then run pytest."

Requires:
    pip install deepagents langchain-ollama rich
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import os  # Environment variable access for provider/model/workdir config
import subprocess  # Spawns child processes — the core of run_shell's execution
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
# InMemorySaver vs MemorySaver: Deep Agents v0.6.x uses InMemorySaver (not
# MemorySaver). Both are in-process checkpointers, but the class name differs
# across versions — check your installed version's docs if this errors.
# ─────────────────────────────────────────────────────────────────────────────
from langgraph.checkpoint.memory import InMemorySaver  # In-process state persistence

# Rich — colored, live terminal output for the streaming view.
from rich.console import Console  # Renders [color] tags + handles input()


console = Console()  # Single shared console instance; reused across all print calls in this script

MAX_OUTPUT_CHARS = 20_000  # ~5k tokens; keeps context window healthy


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


def workspace_root() -> Path:
    """Resolve the sandbox root directory from CODEIT_WORKDIR env var.

    Returns an absolute, resolved Path so subprocess.run gets a clean cwd.
    The .resolve() call normalizes any ../ or ./ in the path and resolves symlinks.
    """
    return Path(os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()


# ─────────────────────────────────────────────────────────────────────────────
# 1. run_shell — a custom @tool. The docstring tells the model WHEN to use it
#    and WHAT the arg is. Tool docstrings are prompts.
#
#    We use shell=True so the model can pass one string with pipes/redirects.
#    This is MORE dangerous (injection) but the agent is constructing the
#    command, and Episode 6 gates it. Trade-off: simplicity vs. safety.
# ─────────────────────────────────────────────────────────────────────────────

@tool
def run_shell(command: str) -> str:
    """Run a shell command in the workspace and return stdout+stderr+exit code.

    Use this to run tests, install packages, execute scripts, or inspect git state.
    Argument: a single shell command string (e.g. 'pytest -q' or 'pip install fastapi').
    The command runs with cwd set to the workspace root.
    Output is truncated if longer than ~20k chars.

    ⚠️ WARNING: This tool has NO approval gate in this episode. The agent can run
    any shell command, including destructive ones like `rm -rf`. Episode 6 adds
    the human-in-the-loop safety gate via interrupt_on + MemorySaver/InMemorySaver.
    """
    # Resolve the working directory — all commands execute here so file ops stay contained.
    cwd = str(workspace_root())

    try:
        proc = subprocess.run(
            command, shell=True,  # Execute via /bin/sh -c (enables pipes/redirects)
            cwd=cwd,  # Confine working directory to the sandbox root
            capture_output=True,  # Capture stdout and stderr separately
            text=True,  # Return strings, not bytes
            timeout=int(os.getenv("CODEIT_SHELL_TIMEOUT", "120")),  # Kill after N seconds
        )
    except subprocess.TimeoutExpired:
        # Timeout is a common failure mode for long-running builds/tests.
        # We return an error string (not raise) so the model can read and adapt.
        return f"Error: command timed out.\nCommand: {command}"
    except Exception as e:
        # Catch-all for other subprocess failures (e.g., binary not found).
        # Returning a string keeps the agent loop alive — it sees the error and retries.
        return f"Error launching command: {type(e).__name__}: {e}"

    out = proc.stdout or ""  # stdout may be None if process produced no output
    err = proc.stderr or ""  # stderr may also be empty for successful commands

    # We return non-zero exits as a STRING, not an exception — the model reads
    # "[exit 1]" and can self-correct (Episode 11 uses this for recovery).
    combined = f"$ {command}\n[exit {proc.returncode}]\n"
    if out:
        combined += f"--- stdout ---\n{out}\n"
    if err:
        combined += f"--- stderr ---\n{err}\n"

    # Truncate output exceeding our character budget — prevents context window overflow.
    if len(combined) > MAX_OUTPUT_CHARS:
        combined = combined[:MAX_OUTPUT_CHARS] + (
            f"\n... [truncated, {len(combined)-MAX_OUTPUT_CHARS} more chars]"
        )

    return combined


# ─────────────────────────────────────────────────────────────────────────────
# 2. Build the agent — FilesystemBackend + our run_shell.
#    This is where we wire everything together: model + tools + backend + checkpointer.
# ─────────────────────────────────────────────────────────────────────────────

def build_agent(workdir: str | None = None):
    """Build a Deep Agents graph with shell execution capability.

    The agent gets two categories of tools:
      - Built-in filesystem tools (ls, read_file, write_file, edit_file, glob, grep)
        provided automatically by FilesystemBackend(virtual_mode=True).
      - Our custom run_shell tool for executing commands in the workspace.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream.
    """
    # Resolve and create the workspace directory — ensures sandbox exists before agent runs.
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    root.mkdir(parents=True, exist_ok=True)

    # FilesystemBackend provides built-in tools with path traversal protection (virtual_mode=True).
    backend = FilesystemBackend(root_dir=str(root), virtual_mode=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[run_shell],  # Custom tool: run shell commands in workspace — NO approval gate yet!
        system_prompt=(
            "You are CodeIt, a coding agent. Use run_shell to run tests, installs, "
            "and git commands. The command runs in the workspace. "
            "Be careful: destructive commands (rm -rf, git push -f) can't be undone."
        ),
        backend=backend,  # Built-in filesystem tools with sandbox ON
        checkpointer=InMemorySaver(),  # In-process state persistence — needed for streaming resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Streaming driver (same shape as Eps 2-4).
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
        prompt: Initial task for the agent (e.g., "Run: echo hello").
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
    """Entry point — build the agent with shell tool and run it.

    The demo prompt asks the agent to echo a message, demonstrating how the model
    constructs a shell command string and our run_shell tool executes it safely
    within the workspace directory.
    """
    # Read the task from CLI args; default to a simple echo so viewers can test immediately.
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Run: echo hello from the shell"

    agent = build_agent()
    state = run(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)

    # ⚠️ WARNING: The agent just ran real shell commands. It COULD have run `rm -rf .`
    # and deleted the workspace. Episode 6 adds the approval gate (interrupt_on + checkpointer).
    print(
        "\n⚠️  The agent just ran real shell commands. It COULD have run `rm -rf .` "
        "and deleted the workspace. Episode 6 adds the approval gate."
    )


if __name__ == "__main__":
    main()
