# Episode 14 — Shipping CodeIt: a Real CLI with Event Streaming

## Overview
**Length:** ~45 minutes  
**Goal:** Ship everything from Episodes 1–13 as a single `codeit` CLI command with a live rich streaming view. The finale where it all comes together.

## What You'll Learn
- **Typer CLI app**: Building a production-style command-line interface with flags (`--provider`, `--model`, `--yolo`, `--workdir`, `--mcp`, `--skills`, `--approve`) using the `typer` library
- **Event streaming view**: Using Deep Agents' event-streaming API (`agent.stream_events(..., version="v3")`) to render live output — tokens stream, tool calls appear in panels, subagent delegations show up, todos update, approval prompts fire
- **Version resilience**: Trying v3 streaming first and falling back to v2 updates if unavailable

## Key Concepts
1. The CLI wraps the full agent pipeline: model factory → filesystem backend → shell tool → approval gate → system prompt → repo map → planning → error recovery → subagents → MCP/skills — all configurable via flags
2. `stream_events(version="v3")` provides granular event types (model stream, tool call, subgraph start/end) that you can render in a rich terminal UI with separate panels for each concern
3. The `--yolo` flag bypasses approval gates; `--approve` auto-approves all gated actions — useful for demos but dangerous on real repos
4. Fallback from v3 to v2 ensures compatibility across Deep Agents versions where the streaming API may differ

## Run Instructions
```bash
# Basic usage with Ollama:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 14-cli-streaming.py run "Add a health endpoint and test it" --provider ollama -m qwen2.5-coder:7b

# Full feature demo with MCP, skills, and auto-approval:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 14-cli-streaming.py run "Build a small FastAPI app" --mcp --skills --approve

# Check all available options:
python 14-cli-streaming.py run --help
```

## Prerequisites
```bash
pip install deepagents langchain-ollama rich python-dotenv typer langchain-mcp-adapters
```