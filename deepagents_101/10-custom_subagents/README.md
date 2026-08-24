# 10 — Customizing Subagents

## Overview
**Goal:** Give subagents their own tools and model, and plug in a pre-compiled LangGraph graph as a subagent — two very different ways to build the same building block.

## What You'll Learn
- **Declarative subagent with its own tools**: `tools` REPLACES the inherited tool set for that subagent (it does not add to it); `model` overrides the orchestrator's model — the place to drop in a cheaper or larger model for the sub-task
- **`CompiledSubAgent`**: pass `runnable=` with anything that compiles to a LangGraph runnable (here a plain `create_agent` haiku writer) — reuse an agent you already built elsewhere, unchanged
- **One request, two subagents**: the orchestrator delegates each sub-task to the right `subagent_type` via the `task` tool

## Key Concepts
1. A subagent's tool list is a replacement, not an addition — define exactly what it needs
2. `description` still drives delegation; the orchestrator picks the subagent by matching the task to it
3. Subagent results come back as `ToolMessage`s named `task`

## Run Instructions
```bash
cd deepagents_101/10-custom_subagents
python 10-custom_subagents.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 10-custom_subagents.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
