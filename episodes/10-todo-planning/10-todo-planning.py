"""
Episode 10 — Planning: TodoList & Task Decomposition
====================================================

The agent learns to plan. Deep Agents' `TodoListMiddleware` is built-in and
always present (it's #1 in the default middleware stack). The `write_todos`
tool is automatically available — we don't add it. We add:
  1. `plan(steps)` — a custom @tool that makes planning EXPLICIT. Returns a
     string telling the model to call `write_todos` with these items as
     pending. (Tools can't call other tools directly — the model orchestrates.)
  2. `complete_todo(id)` — instructs the model to call `write_todos` again
     with item `id` marked `completed`.
  3. `render_todos(state)` — NOT a tool; a helper for the CLI to display state.

⚠️ Assumption: state key is `todos` (some versions use `todo_list` — we check both).
⚠️ Model size: planning is unreliable on ≤8B local models. Use 32b or OpenAI.

Builds on: Episodes 1-9. Requires pip install deepagents langchain-ollama rich.
Run: LLM_MODEL=qwen2.5-coder:32b CODEIT_WORKDIR=./my_project \
     python tutorial.py "Add basic auth: plan 4 steps first."

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
# 1. plan + complete_todo — sugar over the built-in write_todos.
#    Tools can't call other tools directly. We return a STRING instructing
#    the model to call write_todos next; the model then does so.
#
#    WHY THIS PATTERN? Deep Agents' TodoListMiddleware provides a `write_todos`
#    tool that REPLACES the entire todo list (doesn't append). Our plan() and
#    complete_todo() tools can't call write_todos directly — they return strings
#    telling the model what to do. The model then calls write_todos with the right args.
# ─────────────────────────────────────────────────────────────────────────────


@tool
def plan(steps: list[str]) -> str:
    """Plan a multi-step task by seeding the built-in todo list with these steps.

    Use this when the task needs more than one step. Each step becomes a pending todo.
    After planning, execute the steps one by one, calling complete_todo(id) as you finish each.

    Args:
        steps: A list of short step descriptions (e.g., ['read main.py', 'fix bug', 'run tests']).

    Returns: A string instructing the model to call write_todos with these items as pending.
             The model must then execute each step and call complete_todo(id) when done.
    """
    # Format steps as a numbered list for clarity — this is what gets passed to write_todos.
    todo_lines = [f"{i + 1}. {s}" for i, s in enumerate(steps)]

    return (
        "Plan ready. Call write_todos with these items (all status='pending'):\n"
        + "\n".join(todo_lines)
        + "\n\nThen execute each step and call complete_todo(id) when done."
    )


@tool
def complete_todo(id: int) -> str:
    """Mark a todo item as completed by its 1-based index.

    Use this after you finish a step you planned with the plan tool.

    Args:
        id: The 1-based position of the todo in the list (1, 2, 3, ...).

    Returns: A string instructing the model to call write_todos again.
             Note: write_todos REPLACES the list — the model must pass the full list back.
    """
    # write_todos REPLACES the list (doesn't append). The model must pass the
    # full list back with item `id` set to 'completed'. This is a quirk of the API.
    return (
        f"Mark step {id} as completed by calling write_todos with the full list, "
        f"setting item {id}'s status to 'completed'."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. render_todos — NOT a tool. Helper for the CLI to display state.
#    This is called from main() after the agent finishes, so viewers can see
#    what the agent planned and whether it completed all steps.
# ─────────────────────────────────────────────────────────────────────────────


def render_todos(state: dict) -> str:
    """Pretty-print the todo list from agent state. Empty if no todos.

    Reads the 'todos' key (or 'todo_list' fallback for older versions) from
    the final agent state and renders each item with a status marker:
      [x] = completed, [>] = in_progress, [ ] = pending

    Args:
        state: The final agent state dict containing "messages" and optionally "todos".

    Returns: A formatted string of todo items, or "(no todos)" if the list is empty.
    """
    # Check both 'todos' (current) and 'todo_list' (older versions) for compatibility.
    todos = (state or {}).get("todos") or (state or {}).get("todo_list") or []

    if not todos:
        return "(no todos)"

    # Status markers — visual indicators that match the terminal aesthetic.
    marks = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]"}

    lines = []
    for i, t in enumerate(todos, 1):
        status = t.get("status", "pending")  # Default to 'pending' if no status set
        lines.append(f"  {marks.get(status, '[ ]')} {i}. {t.get('content', '')}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Build the agent + streaming + approval driver (same shape as Ep 9).
#    The system prompt instructs the model to plan first, then execute step by step.
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {
    "run_shell": True,
    "write_file": True,
    "edit_file": True,
    "edit_file_safe": True,
    "delete": True,
}


def build_agent(workdir: str | None = None):
    """Build the Deep Agent with planning capability.

    This extends Ep 9's agent by adding plan() and complete_todo() as custom tools
    and updating the system prompt to instruct the model on how to use them for task decomposition.

    The key insight: TodoListMiddleware is ALWAYS present (it's #1 in the default stack),
    so write_todos is always available — we just make it EXPLICIT with our plan() tool.

    Args:
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    # Create the workspace directory if it doesn't exist yet — ensures sandbox is ready
    root.mkdir(parents=True, exist_ok=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[plan, complete_todo],  # Custom planning tools: plan() + complete_todo()
        system_prompt=(
            "You are CodeIt, a coding agent. For any task with more than one step, "
            "call plan([...]) first to seed the todo list, then execute step by step, "
            "calling complete_todo(id) as you finish each. "
            "Use write_todos to update statuses — it REPLACES the list, not appends."
        ),
        backend=FilesystemBackend(  # Built-in filesystem tools with sandbox ON
            root_dir=str(root),  # Confine all file ops to this directory
            virtual_mode=True,  # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        interrupt_on=INTERRUPT_ON,  # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),  # REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Streaming + approval driver (same shape as Eps 6-9).
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
    """Entry point — build the agent with planning capability and run it.

    The demo prompt asks the agent to plan a multi-step task first, demonstrating
    how explicit planning helps break down complex work into manageable steps.
    After completion, we render the todo list so viewers can see what was planned.
    """
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Plan a 3-step task: read main.py, find a bug, run tests. Plan it first."
    )

    agent = build_agent()
    state = run_with_approval(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)

    # Render the todo list so viewers can see what was planned and completed.
    todos_str = render_todos(state or {})
    if todos_str != "(no todos)":
        console.print(f"\n[yellow]todos:[/yellow]\n{todos_str}")


if __name__ == "__main__":
    main()
