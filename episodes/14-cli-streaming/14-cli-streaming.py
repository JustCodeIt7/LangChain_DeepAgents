"""
Episode 14 — Shipping CodeIt: a Real CLI with Event Streaming
==============================================================

The finale. Everything from Eps 1-13 ships as a single `codeit` CLI command
with a live `rich` streaming view. The viewer runs:
    codeit run "add a health endpoint and test it"
and watches the agent work end-to-end: tokens stream, tool calls render in
their own panel, subagent delegations appear, the todo list updates,
approval prompts fire when needed.

New piece: `codeit/cli.py` — a `typer` app with flags (--provider, --model,
--yolo, --workdir, --mcp, --skills, --approve) and a `rich` streaming view
built on Deep Agents' event-streaming API (agent.stream_events(...,
version="v3")). Falls back to v2 updates if v3 is unavailable.

⚠️ Assumption: the v3 event-streaming API may not exist in all installed
versions. We try it first and fall back to v2 — resilience across versions.

Builds on: Episodes 1-13. Requires pip install deepagents langchain-ollama rich typer.
Run: python tutorial.py run "your task" --provider ollama -m qwen2.5-coder:7b -w ./workspace
     python tutorial.py run "build a small FastAPI app" --mcp --skills --approve

Requires: pip install deepagents langchain-ollama rich typer langchain-mcp-adapters.
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import asyncio  # Async event loop — required for MCP tool loading and v3 streaming
import os  # Environment variable access for provider/model/workdir config
import sys  # Command-line argument parsing and stderr output
from pathlib import Path  # Object-oriented filesystem paths with .resolve()

# Typer — modern CLI framework built on Click, used to build the `codeit` command.
import typer  # Declarative CLI: @app.command() + type hints → auto-generated help

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
from rich.panel import Panel  # Boxed containers for tool/assistant messages
from rich.text import Text  # Styled text with color/spans

console = Console()  # Single shared console instance; reused across all print calls in this script
app = typer.Typer(help="CodeIt — your terminal coding agent.")  # Root Typer app for the CLI


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
# 1. A demo custom tool — run_shell. The docstring tells the model WHEN to use it
#    and WHAT the arg is. Tool docstrings are prompts for the model.
#
#    We use shell=True so the model can pass one string with pipes/redirects.
#    This is MORE dangerous (injection) but simpler — Episode 6 gates it.
# ─────────────────────────────────────────────────────────────────────────────

@tool
def run_shell(command: str) -> str:
    """Run a shell command in the workspace. Use for tests, installs, git."""
    import subprocess  # Imported locally to keep top-level imports clean; stdlib, no install needed

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


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tiny MCP loader (async) — graceful degradation. Full version in Ep 13.
#    If no MCP server is configured, returns []. Never raises.
# ─────────────────────────────────────────────────────────────────────────────

async def load_mcp_tools() -> list:
    """Load tools from an MCP server if configured via env vars.

    Reads MCP_SERVER_NAME and MCP_SERVER_URL from the environment. If either
    is missing, returns [] immediately — no error, just empty (graceful degradation).

    This is a simplified version of Ep 13's loader. The full version supports
    multiple servers and transport types (stdio, http, sse). Here we only do
    HTTP for simplicity in the CLI demo.

    Returns: A list of LangChain-compatible tools from the MCP server, or [].
    """
    name = os.getenv("MCP_SERVER_NAME", "")  # Server identifier (e.g., "filesystem")
    url = os.getenv("MCP_SERVER_URL", "")     # HTTP endpoint URL for the MCP server

    if not name or not url:
        return []  # No MCP server configured — skip silently, agent still works with built-ins

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        client = MultiServerMCPClient({name: {"transport": os.getenv("MCP_TRANSPORT", "http"), "url": url}})
        return await client.get_tools()  # Async call — returns LangChain Tool objects
    except Exception as e:
        print(f"MCP tools unavailable: {type(e).__name__}: {e}", file=sys.stderr)
        return []  # Graceful degradation — agent works without MCP tools


# ─────────────────────────────────────────────────────────────────────────────
# 3. Build the agent — all Eps 1-13 wiring in one place.
#    This is where every capability converges: model, filesystem backend,
#    custom tools, approval gate, system prompt, and optional MCP/skills.
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {"run_shell": True, "write_file": True, "edit_file": True, "delete": True}


def build_agent(mcp_tools: list | None = None, skills: list | None = None):
    """Build the Deep Agent with all Episodes 1-13 wiring in one place.

    This is the culmination of the series — every capability from earlier
    episodes converges here: model factory (Ep 1), filesystem backend (Ep 3),
    custom tools (Ep 5), approval gate (Ep 6), system prompt (Ep 7).

    Args:
        mcp_tools: Optional list of MCP-provided LangChain tools. If None, no MCP.
        skills: Optional list of skill directory paths for SkillsMiddleware.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    root = _workspace_root()  # Resolve the sandbox root from CODEIT_WORKDIR env var
    root.mkdir(parents=True, exist_ok=True)  # Create the workspace directory if it doesn't exist yet

    return create_deep_agent(
        model=get_model(),                    # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[run_shell] + (mcp_tools or []),  # Custom tool + optional MCP-provided tools
        system_prompt="You are CodeIt, a terminal coding agent. Use tools when useful.",
        backend=FilesystemBackend(            # Built-in filesystem tools with sandbox ON
            root_dir=str(root),               # Confine all file ops to this directory
            virtual_mode=True,                # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        skills=skills,                        # Optional skill directories for SkillsMiddleware (Ep 13)
        interrupt_on=INTERRUPT_ON,            # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),           # REQUIRED for interrupts; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. The streaming view. Try v3 event-streaming first; fall back to v2 updates.
#    This is the Episode 14 innovation: a rich, panel-based live rendering that
#    shows tool calls and assistant messages in separate colored boxes as they happen.
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


def _render_v2_chunk(chunk):
    """Render a v2 stream chunk using Rich panels (fallback for older versions).

    V2 chunks are dicts with keys: type, ns (node namespace), data.
    We only care about 'updates' — each update contains a snapshot of node state.
    For each message in that state, we render tool calls and assistant text
    inside colored Rich panels for visual clarity.

    This is the fallback path when v3 event streaming isn't available. It's less
    granular than v3 (no token-level streaming) but works across all versions.
    """
    if chunk.get("type") != "updates":  # Skip non-update chunks (e.g., 'values')
        return

    for _n, state in chunk.get("data", {}).items():  # Iterate over node states in this update
        if not isinstance(state, dict):              # Some nodes aren't message-based — skip them
            continue
        for msg in state.get("messages", []):         # Each node may have multiple messages
            if isinstance(msg, AIMessage) and msg.tool_calls:  # Model decided to call a tool
                for tc in msg.tool_calls:
                    console.print(Panel(
                        Text(f"{tc['name']}({tc['args']})", style="magenta"),
                        title="tool", border_style="magenta"
                    ))
            elif isinstance(msg, AIMessage) and msg.content:   # Plain text response from the model
                console.print(Panel(
                    Text(msg.content, style="cyan"),
                    title="assistant", border_style="blue"
                ))


async def _run_streaming(agent, prompt: str, thread_id: str):
    """Drive the agent with event streaming; render each projection in a rich panel.

    This is the Episode 14 showcase — we try v3 event streaming first (which gives
    us token-level interleaving of messages and tool calls), then fall back to v2
    updates if v3 isn't available in the installed Deep Agents version.

    The key innovation: `stream.interleave("messages", "tool_calls")` lets us render
    assistant text and tool invocations IN ORDER as they happen, rather than waiting
    for each node to complete. This gives viewers a real-time view of the agent's thinking.
    """
    config = _config(thread_id)
    input_msg = {"messages": [{"role": "user", "content": prompt}]}

    try:
        # Try v3 event streaming first — this is the modern API that provides
        # fine-grained events (token-by-token messages, individual tool calls).
        stream = agent.stream_events(input_msg, version="v3", config=config)

        # interleave() merges multiple event streams into a single ordered sequence.
        # We ask for "messages" (assistant text tokens) and "tool_calls" (invocations),
        # so they render in the order they actually happened — not batched by node.
        for name, item in stream.interleave("messages", "tool_calls"):
            if name == "messages":
                # Render assistant message token-by-token as it arrives from the model.
                console.print(Panel(
                    Text(getattr(item, "text", str(item)), style="cyan"),
                    title="assistant", border_style="blue"
                ))
            elif name == "tool_calls":
                # Render tool invocation — green if successful, red if it errored.
                color = "green" if getattr(item, "error", None) is None else "red"
                console.print(Panel(
                    Text(f"{item.tool_name}({item.input})", style=color),
                    title="tool", border_style="magenta"
                ))

    except (TypeError, AttributeError):
        # Fallback: v2 updates stream (from Ep 2). If the installed Deep Agents
        # version doesn't have stream_events or interleave, we fall back to the
        # simpler v2 chunk-based streaming that works everywhere.
        for chunk in agent.stream(input_msg, config=config, stream_mode="updates", version="v2"):
            _render_v2_chunk(chunk)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Approval driver (same shape as Eps 6-13) — used when --approve is set.
#    This gives viewers the choice: live streaming view OR approval-gated mode.
# ─────────────────────────────────────────────────────────────────────────────

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


def run_with_approval(agent, prompt: str, thread_id: str = "cli") -> dict:
    """invoke → if interrupted, await_approval → resume. Loops until done.

    This is the human-in-the-loop driver from Episode 6. The flow:
      1. Stream the agent's response (prints live via _render_v2_chunk)
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
        _render_v2_chunk(chunk)

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
            cmd = (Command(resume={"decisions": [{"type": "approve"}]}) if answer == "y"
                   else Command(resume={"decisions": [
                       {"type": "reject", "message": "No."}
                   ]}))

        # Resume the graph with our decision — stream the result and check for more interrupts.
        for chunk in agent.stream(cmd, config=config, stream_mode="updates", version="v2"):
            _render_v2_chunk(chunk)
        state = agent.get_state(config)  # Re-check: did we hit another interrupt?

    return state.values


def _apply_flags(provider: str | None, model: str | None, yolo: bool, workdir: str | None):
    """Mutate env so the rest of the code reads settings as usual (Ep 1 pattern).

    Instead of threading CLI flags through every function call, we set environment
    variables that get_model() and _workspace_root() already read. This keeps the
    agent-building logic identical whether called from CLI or imported as a library.

    Args:
        provider: LLM_PROVIDER override (e.g., "openai")
        model: LLM_MODEL override (e.g., "gpt-4o-mini")
        yolo: If True, set CODEIT_AUTO_APPROVE=true to bypass approval prompts
        workdir: Override for CODEIT_WORKDIR (workspace directory)
    """
    if provider:
        os.environ["LLM_PROVIDER"] = provider
    if model:
        os.environ["LLM_MODEL"] = model
    if yolo:
        os.environ["CODEIT_AUTO_APPROVE"] = "true"
    if workdir:
        os.environ["CODEIT_WORKDIR"] = str(Path(workdir).resolve())


async def _async_main(prompt: str, mcp: bool, skills: bool, approve: bool):
    """Async entry point — loads MCP tools (if requested) then runs the agent.

    The async wrapper is needed because MCP tool loading uses asyncio. Once
    tools are loaded, we build the agent and either run with streaming (default)
    or with approval gate (--approve flag).

    Args:
        prompt: The task for the agent to execute
        mcp: If True, load MCP tools from env-configured server
        skills: If True, load skills from ./skills directory
        approve: If True, use approval-gated mode instead of live streaming
    """
    # Load MCP tools asynchronously if --mcp flag is set. This connects to the
    # MCP server specified by MCP_SERVER_NAME + MCP_SERVER_URL env vars and
    # returns LangChain-compatible tool objects that get registered alongside run_shell.
    mcp_tools = await load_mcp_tools() if mcp else []

    # Skills directory — passed to create_deep_agent's skills parameter for
    # the built-in SkillsMiddleware (Ep 13). If --skills isn't set, pass None.
    skills_paths = ["./skills"] if skills else None

    agent = build_agent(mcp_tools=mcp_tools, skills=skills_paths)

    if approve or os.getenv("CODEIT_AUTO_APPROVE", "false").lower() == "true":
        # Approval-gated mode: stream updates + prompt for each tool call.
        state = run_with_approval(agent, prompt)
        last = state["messages"][-1] if state and "messages" in state else None
        if last:
            print("\n--- final answer ---")
            print(last.content if hasattr(last, "content") else last)
    else:
        # Live streaming mode: token-by-token rendering with v3 fallback to v2.
        await _run_streaming(agent, prompt, thread_id="cli")


@app.command()
def run(
    prompt: str = typer.Argument(..., help="The task for the agent."),
    provider: str = typer.Option(None, "--provider", "-p", help="ollama | openai"),
    model: str = typer.Option(None, "--model", "-m", help="model name"),
    yolo: bool = typer.Option(False, "--yolo", "-y", help="DANGEROUS: auto-approve all actions."),
    workdir: str = typer.Option(None, "--workdir", "-w", help="workspace directory"),
    mcp: bool = typer.Option(False, "--mcp", help="connect to MCP server from env"),
    skills: bool = typer.Option(False, "--skills", help="load skills from ./skills"),
    approve: bool = typer.Option(False, "--approve", help="enable HITL approval gate"),
):
    """Run CodeIt on a task.

    This is the main CLI entry point — Typer auto-generates --help and argument
    parsing from these type hints. The viewer runs `codeit run "task"` with any
    combination of flags to customize behavior.

    Examples:
        codeit run "add a health endpoint" --provider ollama --model qwen2.5-coder:7b
        codeit run "build FastAPI app" --mcp --skills --approve
        CODEIT_AUTO_APPROVE=true codeit run "run tests"  # env var also works
    """
    _apply_flags(provider, model, yolo, workdir)  # Set env vars from CLI flags (Ep 1 pattern)
    asyncio.run(_async_main(prompt, mcp, skills, approve))  # Run the async main coroutine


def main(): app()  # Typer entry point — delegates to the `run` command above

if __name__ == "__main__":
    main()