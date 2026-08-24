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

## Teaching Notes

**Hook:** "The `task` tool spawns a subagent that works in an isolated context — the orchestrator only sees the final answer."

**Walk the cells:**

- **Step 2 — Define a subagent:** Two audiences, two texts. `description` is what the ORCHESTRATOR reads to decide when to delegate (write it like a job posting); `system_prompt` is what the SUBAGENT reads once it's running.
- **Step 3 — Give it to the orchestrator:** `subagents=[...]`. Every deep agent also gets a built-in general-purpose subagent for free.
- **Step 4 — A task worth delegating:** Ask for a critique.
- **Step 5 — See the delegation:** One `task` call out, one consolidated result back. The subagent's internal turns never enter the orchestrator's history.

**On camera:**

- The "Delegation" section — `-> subagent critic` plus the brief — is the payoff. Say the context-isolation point explicitly; it's the whole episode.

**If it goes wrong:**

- The orchestrator may answer the critique itself instead of delegating. The "you MUST delegate" prompt exists for that. If it happens, that's a teaching moment about how strongly to phrase delegation.

**Bridge to ep. 10:** "That subagent used the orchestrator's tools and model. What if it needs its own? Next: customizing subagents."

## Slides & Diagrams

- `slides.md` — 3-slide Marp deck overview of the episode. Preview with the Marp VS Code extension or `npx @marp-team/marp-cli slides.md`
- `diagrams/` — Mermaid sources (`.mmd`) with rendered `.svg`/`.png`: context isolation, the task tool, subagent shape

## Run Instructions

```bash
cd deepagents_101/09-subagents_basics
python 09-subagents_basics.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 09-subagents_basics.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
