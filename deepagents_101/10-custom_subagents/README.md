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

## Teaching Notes

**Hook:** "Give a subagent its own tools and model — or plug in any LangGraph runnable as a subagent."

**Walk the cells:**

- **Step 2 — A tool only the subagent should have:** `celsius_to_fahrenheit`.
- **Step 3 — Declarative subagent with its own tools + model:** `tools` REPLACES the inherited set (doesn't add); `model` overrides the orchestrator's. This is where you'd drop in a cheaper or larger model.
- **Step 4 — A pre-compiled graph:** `CompiledSubAgent` — `runnable=` instead of a prompt. Reuse an agent you built elsewhere, unchanged.
- **Step 5 — Wire both into one orchestrator.**
- **Step 6 — One request, two subagents:** The orchestrator routes each sub-task to the right one.

**On camera:**

- The "Delegations" output showing both `converter` and `poet` is the payoff — one sentence, two specialists.

**If it goes wrong:**

- The orchestrator may send both sub-tasks to one subagent, or answer itself. The coordinator prompt names the routing explicitly ("temperatures to 'converter', poems to 'poet'").

**Bridge to ep. 11:** "So far the agent's answer is prose. What if you need a typed object? Next: structured output."

## Run Instructions

```bash
cd deepagents_101/10-custom_subagents
python 10-custom_subagents.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 10-custom_subagents.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
