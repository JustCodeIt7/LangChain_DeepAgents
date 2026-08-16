"""
Episode 1 — Your Agent's Brain: One File, Two Providers
=======================================================

This is the foundation episode. We build a provider-agnostic model factory that
can switch between Ollama (local) and OpenAI (cloud) via environment variables,
then wrap it in a minimal Deep Agents graph with no tools — just the brain.

Key concepts introduced:
  - get_settings(): reads env vars into a typed Settings dataclass
  - get_model(): branches on provider → calls init_chat_model()
  - build_agent(): thin wrapper around create_deep_agent()
  - main(): CLI demo that invokes the agent and prints the reply

Run:
    LLM_PROVIDER=ollama python tutorial.py "Say hello in one sentence."
    LLM_PROVIDER=openai OPENAI_API_KEY=your-key python tutorial.py "Hello"

Requires: pip install deepagents langchain-ollama rich python-dotenv
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS — each import is annotated with WHY it's needed and verified source.
# This helps viewers understand dependencies without hunting through docs.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations  # PEP 604 union syntax (X | Y) on Python 3.10+

import os  # Environment variable access for provider/model config
import sys  # Command-line argument parsing (sys.argv[1])
from dataclasses import dataclass  # Decorator → typed, immutable config object

# Deep Agents harness — the core framework that compiles a LangGraph agent.
# Verified: `from deepagents import create_deep_agent` (deep-agents-core skill).
from deepagents import create_deep_agent  # Creates compiled agent graph

# load_dotenv reads a local .env file once at import time, if present.
# It's optional — env vars on the command line also work. (python-dotenv)
from dotenv import load_dotenv  # Loads .env into os.environ before we read it

# init_chat_model is LangChain's provider-agnostic factory.
# Verified: `from langchain.chat_models import init_chat_model` (langchain>=1.0).
from langchain.chat_models import init_chat_model  # One call, any provider

# LangChain Core — type hints for model and message objects.
from langchain_core.language_models import BaseChatModel  # Return type of get_model()

# Rich — colored terminal output (print is patched to support [color] tags).
from rich import print  # Drop-in replacement for builtin print with color tag support


load_dotenv()  # Load .env file if present — must run BEFORE any os.getenv calls below


# ─────────────────────────────────────────────────────────────────────────────
# 1. Settings — a tiny typed config loaded from the environment.
#    Using a frozen dataclass gives us immutability (safe to pass anywhere) and
#    type hints for IDE autocomplete, while keeping env var access centralized.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)  # frozen = immutable; safe to pass anywhere without accidental mutation
class Settings:
    """Typed configuration loaded from environment variables.

    This is the Episode 1 settings pattern — a simple dataclass that captures all
    configurable values in one place, with defaults for local development (Ollama).

    Fields:
        llm_provider: "ollama" or "openai" — selects which LLM backend to use
        llm_model: Model name, e.g. "qwen2.5-coder:7b" or "gpt-4o-mini"
        ollama_base_url: Ollama API URL (default: localhost:11434)
        openai_api_key: Required when provider is "openai" — never logged
        openai_base_url: Optional override for OpenAI-compatible endpoints
    """

    llm_provider: str  # "ollama" | "openai"
    llm_model: str  # e.g. "qwen2.5-coder:7b" or "gpt-4o-mini"
    ollama_base_url: str
    openai_api_key: str
    openai_base_url: str


def get_settings() -> Settings:
    """Read settings from env, with sensible defaults for local Ollama.

    This is a FUNCTION (not a cached singleton) so tests can monkeypatch env vars
    and call it fresh — each invocation reads the current environment state.

    Defaults favor Ollama (local LLM server) so viewers can run without an API key:
      - LLM_PROVIDER defaults to "ollama"
      - LLM_MODEL defaults to a small local model
      - OPENAI_API_KEY is empty by default — validated later in get_model()
    """
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "ollama"),  # Default: Ollama (local, no API key)
        llm_model=os.getenv("LLM_MODEL", "qwen3.5:2b"),  # Small model for fast local testing
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),  # Empty by default; validated later
        openai_base_url=os.getenv("OPENAI_BASE_URL", ""),  # Optional override for Azure/etc.
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Model factory — one function, two providers, switched by env only.
#    We pre-build the model ourselves (instead of passing a "provider:model"
#    string to create_deep_agent) so WE own the error messages — e.g. a clear
#    'OPENAI_API_KEY is required' hint instead of a cryptic stack trace.
# ─────────────────────────────────────────────────────────────────────────────

def get_model(settings: Settings | None = None) -> BaseChatModel:
    """Return a chat model for the configured provider.

    This function encapsulates all LLM initialization logic in one place, so
    swapping providers is just an env var change — no code edits needed.

    The pattern: read settings → branch on provider → call init_chat_model()
    with the right kwargs. We validate OPENAI_API_KEY HERE (before calling
    init_chat_model) so the error message is clear and actionable, rather than
    letting it fail deep inside LangChain's HTTP client with a cryptic trace.

    Args:
        settings: Optional Settings override. If None, reads from env via get_settings().

    Returns:
        A BaseChatModel instance ready to pass to create_deep_agent().

    Raises:
        ValueError: If provider is "openai" but OPENAI_API_KEY is not set,
                    or if the provider name is unrecognized.
    """
    s = settings or get_settings()  # Use provided settings or load from env

    if s.llm_provider == "ollama":
        # Ollama runs locally; no API key needed. Make sure `ollama serve` is up.
        return init_chat_model(
            model=s.llm_model,  # e.g., "qwen2.5-coder:7b" — must be pulled via `ollama pull`
            model_provider="ollama",  # Tells LangChain to use the Ollama integration
            base_url=s.ollama_base_url,  # Default: http://localhost:11434
        )

    if s.llm_provider == "openai":
        # OpenAI requires an API key — validate it HERE before calling init_chat_model,
        # so the error message is clear and actionable (not a cryptic HTTP error).
        if not s.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai."
                " Set it in .env or `export OPENAI_API_KEY=...`."
            )

        # Build kwargs dict — base_url is optional (for Azure/OpenAI-compatible endpoints).
        kwargs: dict = {"model": s.llm_model, "model_provider": "openai"}
        if s.openai_base_url:  # Optional override for Azure or self-hosted OpenAI-compatible API
            kwargs["base_url"] = s.openai_base_url

        return init_chat_model(**kwargs)

    # Unknown provider — fail fast with a clear message rather than silently defaulting.
    raise ValueError(f"Unknown LLM_PROVIDER={s.llm_provider!r}. Use 'ollama' or 'openai'.")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Agent builder — thin wrapper around create_deep_agent.
#    This is where we assemble the agent: model + tools + system prompt → compiled graph.
# ─────────────────────────────────────────────────────────────────────────────

def build_agent(model: BaseChatModel | None = None, system_prompt: str | None = None):
    """Build a tool-free Deep Agent. Just the brain.

    create_deep_agent returns a compiled LangGraph graph with .invoke(),
    .stream(), .astream(), .get_state(). We'll use those in later episodes.

    In this episode, tools=[] — no custom tools registered yet. The harness still
    ships built-in planning/filesystem middleware, but with no tools the agent just
    talks (responds to prompts without taking actions). Later episodes add tools one by one.

    Args:
        model: Optional pre-built chat model. If None, calls get_model() to build from env.
        system_prompt: Optional override for the system prompt. Defaults to a helpful assistant.

    Returns: A compiled Deep Agents graph ready to invoke or stream.
    """
    m = model or get_model()  # Use provided model or build one from environment config

    # tools=[] for now — the harness still ships built-in planning/filesystem
    # middleware, but with no custom tools the agent just talks.
    return create_deep_agent(
        model=m,  # Provider-agnostic LLM (Ollama/OpenAI) from get_model()
        tools=[],  # No custom tools yet — later episodes add run_shell, read_summary, etc.
        system_prompt=system_prompt or "You are CodeIt, a helpful coding assistant.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. CLI demo — send one prompt, print the reply.
#    This is the simplest possible agent invocation: invoke() runs to completion.
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point — build a tool-free agent and run it on a single prompt.

    The flow:
      1. Read task from CLI args (default: "Say hello in one sentence.")
      2. Build the agent via build_agent() → get_model() → init_chat_model()
      3. Invoke with thread_id="demo" — runs model→(no tools)→reply to completion
      4. Print the final assistant message

    This demonstrates the minimal viable Deep Agents setup: a model + system prompt,
    no tools, single-turn invocation. Later episodes add streaming (Ep 2), filesystem
    tools (Ep 3+), shell execution (Ep 5), and approval gates (Ep 6).
    """
    # Read the task from CLI args; default demonstrates basic conversation.
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Say hello in one sentence."

    agent = build_agent()

    # thread_id identifies this conversation. Later episodes reuse it for
    # memory and human-in-the-loop interrupts — the checkpointer uses it to
    # group related turns into a single persistent session.
    config = {"configurable": {"thread_id": "demo"}}

    # invoke() runs the full agent loop (model → tool → model → ...) to completion.
    # Unlike stream(), this blocks until the agent finishes — simpler for demos,
    # but you lose live rendering of intermediate steps.
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},  # Initial user message
        config=config,  # Thread ID + any other LangGraph config
    )

    # The final state holds every message; the last one is the agent's reply.
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
