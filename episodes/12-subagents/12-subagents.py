"""
Episode 12 — Sub-Agents: Specialists in Isolated Context
=========================================================

The agent learns to delegate. Deep Agents' `SubAgentMiddleware` is built-in
and the `task` tool is automatically available when subagents are configured.
We add custom subagent specs:
  1. "explorer" — read-only subagent. Tools: build_repo_map (plus the shared
     backend's ls/read_file/grep). No shell, no writes.
  2. "tester"  — run_tests + edit_file_safe. No shell, no write_file.
  3. `spawn_subagent(task, agent)` — sugar over the built-in `task` tool.

Subagents run with isolated context; only a summary returns to the parent.
⚠️ Subagents are STATELESS — give complete instructions in one task call.
⚠️ Model size: delegation needs a larger model — 32b or OpenAI.

Builds on: Episodes 1-11. Requires pip install deepagents langchain-ollama rich.
Run: LLM_MODEL=qwen2.5-coder:32b CODEIT_WORKDIR=./my_project \
     python tutorial.py "Use the explorer subagent to map the codebase."

Requires: pip install deepagents langchain-ollama rich.
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
# 1. Custom tools the subagents will use (trimmed for space; same shape as Eps 5/8/9/11).
#    These are registered on BOTH the parent agent AND specific subagents, depending
#    on what each subagent needs to do. The explorer gets build_repo_map only;
#    the tester gets run_tests + edit_file_safe but NOT shell or write_file.
# ─────────────────────────────────────────────────────────────────────────────


@tool
def run_tests(path: str = ".") -> str:
    """Run pytest in the workspace and return pass/fail summary + failures.

    This is Ep 11's test runner tool — included here so the 'tester' subagent
    can execute tests as part of its isolated workflow. The docstring tells the
    model WHEN to use it: "after editing code with tests."

    Returns a formatted string with exit code, stdout, and stderr. Non-zero exits
    are returned as strings (not exceptions) so the model reads "[exit 1]" and self-corrects.
    """
    try:
        proc = subprocess.run(
            ["pytest", path, "-q", "--tb=short", "--no-header"],
            cwd=str(_workspace_root()),  # Confine to workspace sandbox
            capture_output=True,  # Capture stdout + stderr separately
            text=True,  # Return strings, not bytes
            timeout=180,  # Kill after 3 minutes — tests can take a while
        )
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    # Format output with exit code — the "[exit N]" pattern is what Ep 11's
    # failure detector looks for to trigger self-healing recovery loops.
    return f"$ pytest {path}\n[exit {proc.returncode}]\n{proc.stdout or ''}{proc.stderr or ''}"


@tool
def edit_file_safe(path: str, search: str, replace: str) -> str:
    """Edit a file by replacing `search` with `replace` (first occurrence).

    This is Ep 8's surgical edit tool — included here so the 'tester' subagent
    can fix failing tests without needing full write_file access. The docstring
    tells the model this is for EXISTING files only.

    Returns a success message or an error string if the search text isn't found.
    """
    try:
        fp = _workspace_root() / path  # Resolve within workspace sandbox
        text = fp.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Error: {path} not found."

    if search not in text:
        return f"Could not find search text in {path}. Re-read and retry."

    # Replace only the FIRST occurrence — surgical, targeted edits.
    fp.write_text(text.replace(search, replace, 1), encoding="utf-8")
    return f"Applied exact match edit to {path}."


@tool
def build_repo_map(root: str = ".") -> str:
    """Return a compact map of the codebase: file paths + top-level signatures.

    This is Ep 9's repo mapping tool — included here so the 'explorer' subagent
    can quickly understand project structure without reading every file. The
    docstring tells the model WHEN to use it: "for 'where is X defined?'"

    Uses Python's ast module to extract def/class signatures from .py files,
    walking the workspace directory tree while skipping common noise dirs.
    """
    import ast  # Standard library — parses Python source into an AST for signature extraction

    lines = []
    # Walk the workspace directory tree, following no symlinks (security).
    for dirpath, dirnames, filenames in os.walk(_workspace_root() / root, followlinks=False):
        # Filter out noise directories that add no value to a codebase map.
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".git", ".venv"}]

        for fname in sorted(filenames):
            if not fname.endswith(".py"):  # Only Python files — skip .txt, .md, etc.
                continue

            fp = Path(dirpath) / fname
            try:
                tree = ast.parse(fp.read_text(encoding="utf-8"))  # Parse into AST
            except Exception:
                continue  # Skip files that can't be parsed (syntax errors, encoding issues)

            # Extract top-level function and class definitions from the AST.
            sigs = [f"  def {n.name}()" for n in tree.body if isinstance(n, ast.FunctionDef)]
            sigs += [f"  class {n.name}" for n in tree.body if isinstance(n, ast.ClassDef)]

            # Show relative path + up to 20 signatures per file (keeps output compact).
            lines.append(f"{fp.relative_to(_workspace_root())}:\n" + "\n".join(sigs[:20]))

    return "\n".join(lines) or "(empty workspace)"


# ─────────────────────────────────────────────────────────────────────────────
# 2. spawn_subagent — sugar over the built-in `task` tool. Returns a STRING
#    instructing the model to call task(agent=..., instruction=...).
#    Tools can't call other tools directly — the model orchestrates.
#
#    WHY THIS PATTERN? Deep Agents' SubAgentMiddleware provides a built-in `task`
#    tool that delegates work to specialized subagents. But our custom @tool
#    functions CAN'T call task() directly (tools don't have access to other tools).
#    So spawn_subagent returns a STRING telling the model: "call task with these args."
#    The model then calls task(), and SubAgentMiddleware handles the delegation.
# ─────────────────────────────────────────────────────────────────────────────


@tool
def spawn_subagent(task: str, agent: str = "general-purpose") -> str:
    """Delegate a subtask to a specialized subagent and return its summary.

    Use this for large or isolatable subtasks to keep the main context clean.
    Argument task: a COMPLETE, self-contained description (subagents are stateless).
    Argument agent: 'explorer' (read-only codebase search), 'tester' (run tests + fix),
      or 'general-purpose' (default, same tools as you).

    ⚠️ Subagents are STATELESS — give complete instructions in one task call.
       They don't inherit context from the parent conversation; only what you
       explicitly include in the instruction string is available to them.
    """
    # Return a STRING instructing the model to call the built-in `task` tool.
    # The SubAgentMiddleware intercepts this and routes it to the named subagent.
    return (
        f"To delegate to the '{agent}' subagent, call the task tool with: "
        f"agent='{agent}', instruction='''{task}'''. "
        f"The subagent runs in isolated context and returns only a summary."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Subagent specs — the built-in SubAgentMiddleware reads these.
#    Each spec defines: name, description (for the model to choose), system_prompt,
#    and tools (the subagent's toolbelt — NOT shared with parent or other subagents).
# ─────────────────────────────────────────────────────────────────────────────

SUBAGENTS = [
    {
        "name": "explorer",  # Subagent identifier — referenced by spawn_subagent(agent="explorer")
        # Description is shown to the model when it decides which subagent to use.
        # It should clearly state what this subagent CAN and CANNOT do.
        "description": (
            "Read-only codebase explorer. Use for 'where is X defined?', "
            "'map the codebase'. Returns a summary; cannot modify files or run commands."
        ),
        # System prompt shapes the subagent's behavior — it runs in isolation,
        # so we must explicitly tell it what tools to use and what NOT to do.
        "system_prompt": (
            "You are a read-only codebase explorer. Use ls, read_file, grep, "
            "and build_repo_map. Never write, edit, or run commands. Return a concise summary."
        ),
        # Tools available ONLY to this subagent — the parent agent doesn't see these.
        # The backend's built-in tools (ls, read_file, glob, grep) are always available;
        # we add build_repo_map as an extra custom tool for codebase mapping.
        "tools": [build_repo_map],
    },
    {
        "name": "tester",  # Subagent identifier — referenced by spawn_subagent(agent="tester")
        "description": (
            "Test-runner and fixer. Use for 'make the tests pass'. Can run_tests "
            "and edit existing files, but cannot run shell commands or create new files."
        ),
        "system_prompt": (
            "You are a test runner. Use run_tests; if tests fail, read the failure, "
            "use edit_file_safe to fix, then run_tests again. No run_shell or write_file."
        ),
        # The tester gets run_tests + edit_file_safe — enough to diagnose and fix
        # failing tests without full shell access (which would be dangerous in a subagent).
        "tools": [run_tests, edit_file_safe],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 4. Build the agent — pass subagents to create_deep_agent.
#    The parent agent gets spawn_subagent + all custom tools; each subagent gets
#    only its own toolbelt as defined in SUBAGENTS above.
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {
    "run_shell": True,
    "write_file": True,
    "edit_file": True,
    "edit_file_safe": True,
    "delete": True,
}


def build_agent(workdir: str | None = None):
    """Build the Deep Agent with subagent delegation support.

    This is where everything converges: model factory (Ep 1), filesystem backend
    (Ep 3), custom tools (Eps 5/8/9/11), approval gate (Ep 6), and now subagents
    (Ep 12). The parent agent gets spawn_subagent + all custom tools; each
    subagent in SUBAGENTS gets only its own toolbelt.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    # Create the workspace directory if it doesn't exist yet — ensures sandbox is ready
    root.mkdir(parents=True, exist_ok=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[spawn_subagent, run_tests, edit_file_safe, build_repo_map],  # Parent's toolbelt
        system_prompt=(
            "You are CodeIt, a coding agent. Delegate large or isolatable subtasks "
            "with spawn_subagent. The explorer is read-only; the tester runs tests and fixes."
        ),
        backend=FilesystemBackend(  # Built-in filesystem tools with sandbox ON
            root_dir=str(root),  # Confine all file ops to this directory
            virtual_mode=True,  # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        subagents=SUBAGENTS,  # Subagent specs — each gets its own toolbelt + system prompt
        interrupt_on=INTERRUPT_ON,  # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),  # REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Streaming + approval driver (same shape as Eps 6-11).
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
    """Entry point — build the agent with subagents and run with approval gate.

    The demo prompt asks the agent to use the explorer subagent to map the codebase,
    demonstrating how delegation keeps the parent's context clean while still
    getting a comprehensive view of the project structure.
    """
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Use the explorer subagent to map the codebase."
    agent = build_agent()
    state = run_with_approval(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


if __name__ == "__main__":
    main()
