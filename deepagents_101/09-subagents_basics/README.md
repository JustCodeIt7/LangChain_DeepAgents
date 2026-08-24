# 09 — Delegating to Subagents

## Overview
**Goal:** Spawn a subagent with the `task` tool and see context isolation in action — the orchestrator only sees the final answer, not the scratch work.

## What You'll Learn
- **Defining a subagent**: a `SubAgent` dict with `name`, `description`, `system_prompt` (and optionally `tools`)
- **Two audiences, two texts**: `description` is what the ORCHESTRATOR reads to decide when to delegate (write it like a job posting); `system_prompt` is what the SUBAGENT reads once it is running
- **Context isolation**: one `task` call goes out, one consolidated result comes back; the subagent's internal turns never enter the orchestrator's message history
- **Free subagent**: every deep agent also gets a built-in "general-purpose" subagent; yours are added alongside it

## Key Concepts
1. Isolation is the whole point — long intermediate work stays out of the main context window
2. The orchestrator's system prompt should say WHEN to delegate (e.g. "you MUST delegate critiques to 'critic'")
3. Inspect delegations via `task` tool calls and the `ToolMessage` named `task`

## Run Instructions
```bash
cd deepagents_101/09-subagents_basics
python 09-subagents_basics.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 09-subagents_basics.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
