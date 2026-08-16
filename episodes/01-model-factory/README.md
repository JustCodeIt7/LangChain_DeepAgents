# Episode 1 — Your Agent's Brain: One File, Two Providers

## Overview
**Length:** ~12 minutes  
**Goal:** Build the foundation of a coding agent — a provider-agnostic model factory that switches between local Ollama and cloud OpenAI via environment variables.

## What You'll Learn
- **Settings dataclass**: Typed configuration loaded from env vars with `frozen=True` for immutability
- **`get_model()`**: One function, two providers (Ollama/OpenAI), switched by `LLM_PROVIDER` env var
- **`build_agent()`**: Thin wrapper around `create_deep_agent()` — returns a compiled LangGraph graph
- **CLI demo**: Using `agent.invoke()` to run the agent synchronously

## Key Concepts
1. Provider-agnostic model factory: switch between Ollama and OpenAI with just env vars
2. Pre-build the model so you own error messages (clear hints vs cryptic stack traces)
3. Validate API keys BEFORE any network call — fail fast with helpful messages
4. `create_deep_agent` returns a compiled LangGraph graph with `.invoke()`, `.stream()`, and `.get_state()`

## Run Instructions
```bash
# Local Ollama (default):
LLM_PROVIDER=ollama python 01-model-factory.py "Say hello in one sentence."

# Cloud OpenAI:
LLM_PROVIDER=openai OPENAI_API_KEY=your-key LLM_MODEL=gpt-4o-mini \
    python 01-model-factory.py "Say hello in one sentence."
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Provider selector: `ollama` or `openai` |
| `LLM_MODEL` | `qwen3.5:2b` | Model name (e.g., `gpt-4o-mini`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `OPENAI_API_KEY` | *(empty)* | Required when `LLM_PROVIDER=openai` |
| `OPENAI_BASE_URL` | *(empty)* | Optional override for OpenAI-compatible endpoints |

## Prerequisites
```bash
pip install deepagents langchain-ollama rich python-dotenv
```