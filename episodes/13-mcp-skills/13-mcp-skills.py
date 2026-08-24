"""
Episode 13 — MCP + Skills: Speaking the Standard Protocol
==========================================================

The agent gains two capabilities from the Deep Agents ecosystem:
  1. MCP tools — connect to an MCP server via `langchain-mcp-adapters`. The
     server's tools register alongside our custom tools, exposed automatically.
  2. Skills — a `skills/` directory with one example `SKILL.md` (YAML
     frontmatter + markdown instructions). `SkillsMiddleware` (built-in, #2
     in the default stack) loads skill summaries at startup and the agent
     reads full instructions on demand. Progressive disclosure: context
     stays small until a skill is needed.

New pieces:
  1. `build_mcp_config(settings)` + `load_mcp_tools(config)` (async) helpers.
  2. `skills/python-testing/SKILL.md` (created by the viewer; we show the format).
  3. Extended `build_agent()` — accepts `mcp_tools` and `skills` lists.

Both are OPTIONAL — the agent works without them. Graceful degradation is
the contract: if no MCP server is configured or it's down, load_mcp_tools
returns []; if no skills directory is passed, SkillsMiddleware skips.

⚠️ MCP tool loading is ASYNC — `get_tools()` is a coroutine. The demo uses
asyncio.run to wrap the async loading before calling build_agent.

Builds on: Episodes 1-12. Requires pip install deepagents langchain-ollama rich langchain-mcp-adapters.
Run: see `python tutorial.py --help`. Demo needs an MCP server (e.g. npx
     @modelcontextprotocol/server-filesystem ./workspace) on MCP_SERVER_URL.

Requires: pip install deepagents langchain-ollama rich langchain-mcp-adapters.
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import asyncio  # Async event loop — required for MCP tool loading (get_tools is a coroutine)
import os  # Environment variable access for provider/model/workdir config
import sys  # Command-line argument parsing and stderr output
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
# 1. MCP config + tool loading. MCP is OPTIONAL — graceful degradation.
#
#    WHAT IS MCP? The Model Context Protocol (MCP) is an open standard for
#    connecting LLMs to external data sources and tools. An MCP server exposes
#    a set of "tools" that the agent can call — e.g., reading files, querying
#    databases, running commands on a remote machine.
#
#    The langchain-mcp-adapters package bridges MCP servers into LangChain's
#    Tool interface, so they work seamlessly alongside our custom @tool functions.
# ─────────────────────────────────────────────────────────────────────────────


def build_mcp_config() -> dict | None:
    """Build the MultiServerMCPClient config from env. None if no server configured.

    Reads MCP_SERVER_NAME, MCP_TRANSPORT, MCP_SERVER_URL from env.
    Example .env: MCP_SERVER_NAME=filesystem, MCP_TRANSPORT=http,
                  MCP_SERVER_URL=http://localhost:8000/mcp

    Returns a dict suitable for MultiServerMCPClient(config), or None if no
    server is configured (graceful degradation — agent works without MCP).
    """
    name = os.getenv("MCP_SERVER_NAME", "")  # Server identifier (e.g., "filesystem")
    url = os.getenv("MCP_SERVER_URL", "")  # HTTP endpoint URL for the MCP server
    transport = os.getenv("MCP_TRANSPORT", "http")  # Transport type: http, sse, or stdio

    if not name or not url:
        return None  # No MCP server configured — agent will work with built-in tools only

    # The config dict maps server names to their connection parameters.
    # MultiServerMCPClient uses this to connect and discover available tools.
    return {name: {"transport": transport, "url": url}}


async def load_mcp_tools(config: dict | None = None) -> list:
    """Connect to the MCP server(s) and return their tools. Empty list if no config.

    This is an ASYNC function because MCP's get_tools() is a coroutine — it makes
    network calls to discover available tools from the server. We use asyncio.run()
    in main() to wrap this async call before passing results to build_agent().

    Graceful degradation: if the server is unreachable or returns no tools, we
    print an error to stderr and return []. The agent continues with just its
    built-in FilesystemBackend tools + our custom run_shell.

    Args:
        config: MCP client config dict from build_mcp_config(), or None.

    Returns: A list of LangChain-compatible Tool objects from the MCP server, or [].
    """
    if not config:
        return []  # No config — skip silently (graceful degradation)

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient(config)
        return await client.get_tools()  # Async call — returns LangChain Tool objects
    except Exception as e:
        # Server unreachable, wrong URL, or connection refused. We degrade gracefully
        # rather than crashing — the agent still has its built-in tools to work with.
        print(f"MCP tools unavailable: {type(e).__name__}: {e}", file=sys.stderr)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 2. A demo custom tool (so the agent can do something even with no MCP server).
#    This is the same run_shell from Ep 5 — included so the agent has a useful
#    action available regardless of whether an MCP server is configured.
# ─────────────────────────────────────────────────────────────────────────────


@tool
def run_shell(command: str) -> str:
    """Run a shell command in the workspace. Use for tests, installs, git."""
    import subprocess  # Imported locally to keep top-level imports clean; stdlib, no install needed

    try:
        proc = subprocess.run(
            command,
            shell=True,  # Execute via /bin/sh -c (enables pipes/redirects)
            cwd=str(_workspace_root()),  # Confine working directory to the sandbox root
            capture_output=True,  # Capture stdout and stderr separately
            text=True,  # Return strings, not bytes
            timeout=120,  # Kill after 2 minutes — prevents hanging commands
        )
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    return f"$ {command}\n[exit {proc.returncode}]\n{proc.stdout or ''}{proc.stderr or ''}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Build the agent — mcp_tools + skills are optional lists.
#    This is where MCP tools and skill directories get wired into the Deep Agent.
#    Both parameters default to None, so the agent works without them (graceful degradation).
# ─────────────────────────────────────────────────────────────────────────────

INTERRUPT_ON = {"run_shell": True, "write_file": True, "edit_file": True, "delete": True}


def build_agent(
    mcp_tools: list | None = None,
    skills: list | None = None,
    workdir: str | None = None,
):
    """Build the Deep Agent with MCP tools and skills support.

    This extends Ep 12's agent builder by accepting two new optional parameters:
      - mcp_tools: LangChain Tool objects from an MCP server (loaded async in main)
      - skills: list of directory paths containing SKILL.md files for SkillsMiddleware

    Both are OPTIONAL — if None, the agent works with just its built-in tools.
    This is the graceful degradation contract: missing MCP server or no skills
    directory → agent still functions, just without those extra capabilities.

    Args:
        mcp_tools: Optional list of LangChain-compatible tools from an MCP server.
        skills: Optional list of skill directory paths (e.g., ["./skills"]).
        workdir: Optional override for CODEIT_WORKDIR. If None, reads from env.

    Returns: A compiled Deep Agents graph ready to stream or invoke.
    """
    root = Path(workdir or os.getenv("CODEIT_WORKDIR", "./workspace")).resolve()
    # Create the workspace directory if it doesn't exist yet — ensures sandbox is ready
    root.mkdir(parents=True, exist_ok=True)

    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[run_shell] + (mcp_tools or []),  # Custom tool + optional MCP-provided tools
        system_prompt=(
            "You are CodeIt, a coding agent. MCP tools (if present) come from an external "
            "server. Skills load on demand when relevant."
        ),
        backend=FilesystemBackend(  # Built-in filesystem tools with sandbox ON
            root_dir=str(root),  # Confine all file ops to this directory
            virtual_mode=True,  # ⚠️ CRITICAL: path traversal protection (../, ~/, abs paths)
        ),
        skills=skills,  # list of directory paths; None = no skills
        interrupt_on=INTERRUPT_ON,  # Approval gate — pauses on dangerous tools (Ep 6)
        checkpointer=MemorySaver(),  # REQUIRED for interrupts to work; persists state across resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Streaming + approval driver (same shape as Eps 6-12).
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
# 5. main — async entry point because MCP tool loading is async.
#    The demo uses --mcp and --skills flags to toggle these optional capabilities.
# ─────────────────────────────────────────────────────────────────────────────


async def _async_main(prompt: str, use_mcp: bool, skills_dir: str | None):
    """Async main — loads MCP tools (if requested) then runs the agent with approval gate.

    The async wrapper is needed because MCP tool loading uses asyncio. Once
    tools are loaded, we build the agent and run it through the approval driver.

    Args:
        prompt: The task for the agent to execute
        use_mcp: If True, load MCP tools from env-configured server
        skills_dir: Optional path to a skills directory (e.g., "./skills")
    """
    # Load MCP tools asynchronously if --mcp flag is set. This connects to the
    # MCP server specified by MCP_SERVER_NAME + MCP_SERVER_URL env vars and
    # returns LangChain-compatible tool objects that get registered alongside run_shell.
    mcp_tools = await load_mcp_tools(build_mcp_config()) if use_mcp else []

    if use_mcp:
        console.print(
            f"[dim]Loaded {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}[/dim]"
        )

    # Skills directory — passed to create_deep_agent's skills parameter for
    # the built-in SkillsMiddleware. If --skills isn't set, pass None (no skills).
    skills = [skills_dir] if skills_dir else None

    agent = build_agent(mcp_tools=mcp_tools, skills=skills)
    state = run_with_approval(agent, prompt)

    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


def main() -> None:
    """Entry point — parse CLI args, load MCP tools async, run the agent.

    The demo supports two optional flags:
      --mcp   : Connect to an MCP server (requires MCP_SERVER_NAME + URL env vars)
      --skills: Load skills from ./skills directory (Ep 13 progressive disclosure)

    Both are OPTIONAL — without them, the agent works with just its built-in tools.
    """
    prompt = sys.argv[1] if len(sys.argv) > 1 else "What MCP tools do you have? Use them if useful."
    # Check for --mcp flag (simple string check, no argparse needed)
    use_mcp = "--mcp" in sys.argv
    skills_dir = "./skills" if "--skills" in sys.argv else None

    asyncio.run(_async_main(prompt, use_mcp, skills_dir))  # Run the async main coroutine


if __name__ == "__main__":
    main()
