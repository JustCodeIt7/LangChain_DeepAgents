"""
Episode 2 — The Agentic Loop, Made Visible
==========================================

We drive the Deep Agents graph with `agent.stream(stream_mode="updates",
version="v2")` so each step of the loop (model request → tool call → tool
result → final answer) prints live. A tiny `get_time` @tool proves the loop
fires: the model DECIDES to call it, the tool runs, the model reads the result
and answers. That's what makes it an agent, not a chatbot.

Builds on: Episode 1 (get_model, build_agent).

Run:
    LLM_PROVIDER=ollama LLM_MODEL=qwen2.5-coder:7b \
        python agentic-loop.py "What time is it? Use your tool."

Requires:
    pip install deepagents langchain-ollama rich
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import os  # Environment variable access for provider/model config
import sys  # Command-line argument parsing (sys.argv[1])

# Deep Agents harness — the core framework that compiles a LangGraph agent.
from deepagents import create_deep_agent  # Creates compiled agent graph

# ─────────────────────────────────────────────────────────────────────────────
# Reuse the Episode 1 model factory + settings. In a real codebase these
# would live in codeit/ package; here we inline a trimmed copy so this file
# is self-contained — each episode script runs independently for YouTube viewers.
# ─────────────────────────────────────────────────────────────────────────────
# LangChain — provider-agnostic LLM integration and tool definitions.
from langchain.chat_models import init_chat_model  # One call, any provider

# `tool` decorator turns a plain function into a LangChain tool whose
# docstring becomes the schema description the model sees.
# Verified: `from langchain.tools import tool` (langchain>=1.0).
from langchain.tools import tool

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
    model_name = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")

    if provider == "openai":
        # OpenAI requires an API key — we validate it HERE, before calling
        # init_chat_model, so the error message is clear and actionable.
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY required when LLM_PROVIDER=openai.")

        return init_chat_model(model=model_name, model_provider="openai")

    # Default: Ollama (local LLM server). We pass base_url so viewers can point
    # at a remote Ollama instance if needed (e.g., in a VM or container).
    return init_chat_model(
        model=model_name,
        model_provider="ollama",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. A demo tool — the docstring is FOR THE MODEL. It tells the model WHEN
#    to call this tool and what it returns. Tool docstrings are prompts.
#
#    WHY THIS MATTERS: The @tool decorator wraps a plain function so Deep Agents
#    can expose it to the LLM. When the model decides "I need the time", it emits
#    a structured tool_call — that's what makes this an agent, not just a chatbot.
# ─────────────────────────────────────────────────────────────────────────────

@tool
def get_time() -> str:
    """Return the current time. Use this when the user asks for the time."""
    # datetime is imported locally to keep top-level imports clean; stdlib, no install needed.
    import datetime

    return datetime.datetime.now().isoformat(timespec="seconds")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Build the agent — same as Ep 1, but now we register get_time.
#    This is where tools=[get_time] makes the tool available to the model.
# ─────────────────────────────────────────────────────────────────────────────

def build_agent():
    """Build a Deep Agents graph with one custom tool (get_time).

    The agent gets:
      - A provider-agnostic LLM from get_model() (Ollama/OpenAI)
      - One custom @tool: get_time — demonstrates the model→tool→model loop
      - MemorySaver checkpointer for state persistence across streaming resume

    Returns: A compiled Deep Agents graph ready to stream.
    """
    return create_deep_agent(
        model=get_model(),  # Provider-agnostic LLM (Ollama/OpenAI) from Ep 1
        tools=[get_time],  # ← Register our custom tool — the model can now call it!
        system_prompt="You are CodeIt, a helpful coding assistant. Use tools when useful.",
        checkpointer=MemorySaver(),  # In-process state persistence — needed for streaming resume
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. The streaming driver — prints each graph node event live with rich.
#    This is the core of Episode 2: making the agentic loop VISIBLE to viewers.
# ─────────────────────────────────────────────────────────────────────────────

def _config(thread_id: str) -> dict:
    """Build the LangGraph config dict with thread ID + recursion limit.

    - configurable.thread_id: groups related turns into a conversation thread
      (required for MemorySaver to persist state across resume).
    - recursion_limit: caps total super-steps so a looping model can't hang.
      Default 25 × 2 = 50 (each step ≈ 2 super-steps: model call + tool exec).

    NOTE: recursion_limit is a TOP-LEVEL config key, NOT inside configurable.
    It counts super-steps (model call + tool exec ≈ 2). We cap it so a
    looping model can't hang the viewer's machine.
    """
    max_iters = int(os.getenv("CODEIT_MAX_ITERS", "25"))
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": max_iters * 2,
    }


def _print_event(chunk) -> None:
    """Pretty-print one v2 stream chunk to the console.

    V2 chunks are dicts with keys: type, ns (node namespace), data.
    We only care about 'updates' — each update contains a snapshot of node state.
    For each message in that state, we render tool calls and assistant text.

    This function is called for EVERY chunk the stream emits, giving us live
    rendering as the agent thinks, calls tools, and responds.
    """
    kind = chunk.get("type")  # 'updates' or 'values' — we only handle updates here
    if kind != "updates":
        return

    for _node_name, state in chunk.get("data", {}).items():  # Iterate over node states
        if not isinstance(state, dict):  # Some nodes aren't message-based — skip them
            continue
        for msg in state.get("messages", []):  # Each node may have multiple messages
            if isinstance(msg, AIMessage) and msg.tool_calls:  # Model decided to call a tool
                for tc in msg.tool_calls:
                    console.print(f"[cyan]tool call:[/cyan] {tc['name']}({tc['args']})")
            elif isinstance(msg, AIMessage) and msg.content:  # Plain text response from the model
                console.print(f"[green]assistant:[/green] {msg.content}")


def run(agent, prompt: str, thread_id: str = "default") -> dict:
    """Drive the agent with streaming so each node event prints live.

    The flow:
      1. Stream with stream_mode='updates' — each chunk is a node state snapshot.
      2. _print_event renders tool calls and assistant messages as they happen.
      3. After streaming completes (or errors), return final state values.

    Args:
        agent: The compiled Deep Agents graph from build_agent().
        prompt: Initial task for the agent (e.g., "What time is it?").
        thread_id: Conversation thread ID — must match across stream/resume calls.

    Returns: Final agent state dict with messages and values.
    """
    config = _config(thread_id)

    try:
        # Stream in 'updates' mode — fires on each node execution, giving us live rendering.
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": prompt}]},  # Initial user message
            config=config, stream_mode="updates", version="v2",  # v2 = typed dicts
        ):
            _print_event(chunk)  # Render each chunk as it arrives — live output!
    except Exception as e:
        # GraphRecursionError or model errors — print clearly, don't crash.
        console.print(f"[red]error:[/red] {type(e).__name__}: {e}")

    # Fetch the final state for the return value — get_state() reads from MemorySaver.
    return agent.get_state(config).values


# ─────────────────────────────────────────────────────────────────────────────
# 4. CLI demo.
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point — build the agent with a tool and run it interactively.

    The demo prompt asks for the time, demonstrating how the model DECIDES to call
    get_time (not just answer from training data), then reads the result and responds.
    This is what makes it an agent: autonomous tool use driven by reasoning.
    """
    # Read the task from CLI args; default demonstrates the tool-calling loop.
    prompt = sys.argv[1] if len(sys.argv) > 1 else "What time is it? Use your tool."

    agent = build_agent()
    state = run(agent, prompt)

    # Extract and print the final assistant message from the conversation history.
    last = state["messages"][-1] if state and "messages" in state else None
    if last:
        print("\n--- final answer ---")
        print(last.content if hasattr(last, "content") else last)


if __name__ == "__main__":
    main()
