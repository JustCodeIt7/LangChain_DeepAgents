"""
Episode 7 — The System Prompt: engineering personality & rules
==============================================================

The agent gets a REAL system prompt — personality, tool-use policy, safety
rules, editing conventions. We also load project-specific context from
`AGENTS.md` (Deep Agents' own convention) or `CODEIT.md` fallback in the
workspace, and compose the two. The harness's own middleware injects its own
tool descriptions on top of our system_prompt; we ADD policy, not replace it.

Builds on: Episodes 1-6.

Run:
    # Add an AGENTS.md to your workspace first, e.g.:
    #   echo '# My project\\nUse FastAPI. The bug is in main.py.' > workspace/AGENTS.md
    CODEIT_WORKDIR=./workspace python tutorial.py "What is this project? Fix the failing test."

Requires: pip install deepagents langchain-ollama rich.
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


# ─────────────────────────────────────────────────────────────────────────────
# 1. SYSTEM_PROMPT — written for the MODEL, not for the viewer. Imperative, short.
#    This is the agent's personality and rulebook. It tells the model WHO to be,
#    HOW to use tools, WHAT safety rules to follow, and HOW to communicate.
#
#    KEY PRINCIPLE: The system prompt is a PROMPT — it shapes the model's behavior.
#    Every instruction here becomes part of what the model sees as its directive.
#    Write imperatively ("Use write_file only for new files") not descriptively.
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are CodeIt, a terminal coding agent.

# Role
You help the user write, edit, and run code in their workspace. You read files,
write files, run shell commands, and plan multi-step tasks.

# Tool-use policy
- Prefer the built-in filesystem tools (ls, read_file, grep, glob) for exploration.
- Use write_file only for new files. Use edit_file for changes to existing files.
- Use run_shell for tests, installs, and git operations. The user will be asked
  to approve mutating or destructive commands — prefer the least destructive option.
- Use write_todos to plan any task that needs more than one step.

# Safety
- Never run destructive commands (rm -rf, git push -f, dd, mkfs) without explaining why.
- If a command might modify files outside the workspace, say so and stop.
- The user can reject any action. Accept rejection gracefully and try a safer approach.

# Editing rules
- For small targeted changes, use edit_file (search-replace). Never rewrite a whole
  file to change a few lines.
- After editing code that has tests, run the tests with run_shell('pytest -q') and fix failures.

# Communication
- Be concise. Say what you're about to do, do it, then summarize the result in one line.
- When a tool call fails, read the error, explain what went wrong in one sentence, and retry.
- Don't apologize; fix.
"""


# ─────────────────────────────────────────────────────────────────────────────
# 2. load_project_context — read AGENTS.md (Deep Agents convention) or
#    CODEIT.md fallback from the workspace. Graceful: missing file → "".
#
#    WHAT IS AGENTS.md? It's a Deep Agents convention for project-specific instructions.
#    If present in the workspace, its contents are appended to the system prompt so the
#    agent knows about project conventions (e.g., "Use FastAPI", "The bug is in main.py").
# ─────────────────────────────────────────────────────────────────────────────


def load_project_context(root: str | Path | None = None) -> str:
    """Read AGENTS.md (or CODEIT.md fallback) from the workspace. '' if absent.

    This function implements graceful degradation — if neither file exists, it returns
    an empty string and the agent works with just SYSTEM_PROMPT. If a file is found but
    can't be read (permissions, encoding), we also return "" rather than crashing.

    The project context is APPENDED to SYSTEM_PROMPT via build_system_prompt(), so the
    model sees both the general rules AND the project-specific instructions in one prompt.

    Args:
        root: Workspace directory path. If None, reads from CODEIT_WORKDIR env var.

    Returns: A formatted string with the file contents prefixed by a header, or "".
    """
    r = Path(root or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()

    # Check for AGENTS.md first (Deep Agents convention), then CODEIT.md as fallback.
    # If both exist, AGENTS.md wins — it's the standard name in the Deep Agents ecosystem.
    for name in ("AGENTS.md", "CODEIT.md"):
        candidate = r / name
        if candidate.is_file():
            try:
                return f"\n\n# Project context ({name})\n\n" + candidate.read_text(encoding="utf-8")
            except Exception:
                return ""  # Degrade gracefully — don't crash on read errors

    return ""  # No project context file found — agent works with SYSTEM_PROMPT only


def build_system_prompt(root: str | Path | None = None) -> str:
    """Compose the harness system prompt with any project context.

    This concatenates SYSTEM_PROMPT (general rules for all projects) with load_project_context()
    (project-specific instructions from AGENTS.md/CODEIT.md). The result is passed to
    create_deep_agent's system_prompt parameter, which becomes part of what the model sees.

    Note: Deep Agents' middleware ALSO injects its own tool descriptions on top of this —
    we ADD policy here, not replace it. Our prompt shapes behavior; the harness handles mechanics.

    Args:
        root: Workspace directory path for loading project context. If None, uses env var.

    Returns: The composed system prompt string (SYSTEM_PROMPT + optional project context).
    """
    return SYSTEM_PROMPT + load_project_context(root)


# ─────────────────────────────────────────────────────────────────────────────
# 3. A demo custom tool — run_shell. The docstring tells the model WHEN to use it
#    and WHAT the arg is. Tool docstrings are prompts for the model.
#
#    We use shell=True so the model can pass one string with pipes/redirects.
#    This is MORE dangerous (injection) but simpler — Episode 6 gates it.
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
# 4. Build the agent — compose system prompt + project context, wire up tools.
#    The key difference from Ep 6: we pass build_system_prompt(root) instead of a static string.
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {"run_shell": True, "write_file": True, "edit_file": True, "delete": True}


def build_agent(workdir: str | None = None):
    """Build the Deep Agent with system prompt + project context composition.

    This extends Ep 6's agent by replacing the static system_prompt string with a
    composed one that includes both general rules (SYSTEM_PROMPT) and any project-specific
    instructions from AGENTS.md/CODEIT.md in the workspace.

    The key insight: build_system_prompt() is called at BUILD TIME, not runtime — so if
    the viewer adds an AGENTS.md after building the agent, they need to rebuild it.
    This matches how real coding agents work: project context is loaded once per session.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    # Create the workspace directory if it doesn't exist yet — ensures sandbox is ready
    root.mkdir(parents=True, exist_ok=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[run_shell],  # Custom tool: run shell commands in workspace (Ep 5)
        system_prompt=build_system_prompt(
            root
        ),  # ← COMPOSED prompt: SYSTEM_PROMPT + AGENTS.md/CODEIT.md
        backend=FilesystemBackend(  # Built-in filesystem tools with sandbox ON
            root_dir=str(root),  # Confine all file ops to this directory
            virtual_mode=True,  # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        interrupt_on=INTERRUPT_ON,  # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),  # REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Streaming + approval driver (same shape as Eps 6).
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
        if pending is None:
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
            if answer == "y":
                cmd = Command(resume={"decisions": [{"type": "approve"}]})
            else:
                cmd = Command(resume={"decisions": [{"type": "reject", "message": "No."}]})

        # Resume the graph with our decision — stream the result and check for more interrupts.
        for chunk in agent.stream(cmd, config=config, stream_mode="updates", version="v2"):
            _print_event(chunk)
        state = agent.get_state(config)  # Re-check: did we hit another interrupt?

    return state.values


def main() -> None:
    """Entry point — build the agent with system prompt + project context and run it.

    The demo asks "What is this project?" — if an AGENTS.md exists in the workspace,
    the agent reads it via load_project_context() and uses those instructions.
    """
    prompt = sys.argv[1] if len(sys.argv) > 1 else "What is this project?"

    agent = build_agent()
    state = run_with_approval(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


if __name__ == "__main__":
    main()
