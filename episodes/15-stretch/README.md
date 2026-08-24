# Episode 15 — LangSmith Observability Appendix

## Overview

**Length:** ~20 minutes  
**Goal:** Show viewers how to see what the agent is doing under the hood. With LangSmith tracing enabled, every model call, tool invocation, subagent delegation, and message history becomes visible in a trace URL you can open in the browser.

## What You'll Learn

- **LangSmith tracing**: Enabling `LANGSMITH_TRACING=true` to capture full execution traces of agent runs
- **`trace_url_for_run(run_id)`**: A helper that constructs a clickable LangSmith dashboard URL for a specific run ID
- **`maybe_print_trace_url(state)`**: Inspects the final agent state and prints the trace URL if tracing is enabled

## Key Concepts

1. Tracing makes the invisible visible: you can see exactly which tools were called, in what order, with what arguments, and how long each step took — invaluable for debugging and teaching
2. LangSmith is already a dependency from earlier episodes; no new installation needed beyond setting environment variables
3. Environment variable names are `LANGSMITH_*` (per the ecosystem-primer skill) — older `LANGCHAIN_API_KEY` / `LANGCHAIN_TRACING` names no longer work
4. The trace URL shape may change over time; if it doesn't open, direct viewers to the LangSmith dashboard and have them find the run by project name + timestamp

## Run Instructions

```bash
# Set up tracing environment variables:
export LANGSMITH_API_KEY=your-langsmith-api-key
export LANGSMITH_TRACING=true
export LANGSMITH_PROJECT=codeit-demo

# Create workspace with a sample app to debug:
mkdir -p ./workspace && echo "def add(a, b):\n    return a * b  # Bug" > ./workspace/main.py

# Run the agent and get a trace URL at the end:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 15-stretch.py "Fix the bug in main.py. The add function should return the sum."

# Open the printed trace URL to see the full execution graph in LangSmith.
```

## Prerequisites

```bash
pip install deepagents langchain-ollama rich python-dotenv langsmith
```
