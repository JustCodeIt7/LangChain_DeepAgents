# 01 — Your First Deep Agent

## Overview

**Goal:** Create a working deep agent with a single function call and inspect what it does under the hood.

## What You'll Learn

- **`create_deep_agent()`**: the single entry point of the framework — `model` + `system_prompt` is all you need
- **The built-in tool suite**: `ls`/`read_file`/`write_file`/`edit_file`/`delete`/`glob`/`grep`, plus `execute`, `task`, and `write_todos` — no `tools=` argument required
- **The state shape**: `agent.invoke({"messages": [...]})` returns a dict; `messages` is the full conversation, `files` is the agent's virtual filesystem
- **`text_of()`**: normalizing message content across providers (Ollama returns a string, OpenAI returns content blocks)

## Key Concepts

1. A deep agent is a regular LangChain agent **plus** a built-in tool suite — the tools come for free
2. The agent's filesystem is virtual by default (lives in graph state, not on disk — see ep. 05)
3. `result["messages"][-1]` is the final answer; earlier messages include every tool call

## Teaching Notes

**Hook:** "One function call gives you an agent with a filesystem, planning, and subagents. Here's the entire framework surface for episode one."

**Walk the cells** (the `# %%` markers let you run cell by cell):

- **Step 1 — Imports:** `create_deep_agent` is the only import from deepagents. Point at `text_of()` and call it out as boilerplate that recurs in every episode: Ollama returns a string, OpenAI returns content blocks, so we normalize both.
- **Step 2 — What's in the box:** Read the `BUILT_IN_TOOLS` dict out loud — this is the "what you get for free" slide. Emphasize: there is no `tools=` argument anywhere in this script.
- **Step 3 — Create the agent:** Only `model` + `system_prompt`. Point at the _absence_ of `tools=` — that's the whole point of a deep agent.
- **Step 4 — Run it:** Input is `{"messages": [...]}`, exactly like any LangChain agent. Note the "answer directly without using any tools" instruction — it keeps the first demo fast and predictable.
- **Step 5 — Inspect:** `result` is a state dict. `messages` = the full conversation; `files` = the virtual filesystem (empty here — plant the seed for ep. 05).

**On camera:**

- The message trace (Human → AI) is the payoff — show that the "conversation" is just a list of message objects you can iterate.
- Let the final answer land, then zoom out: "That's everything you need to create a deep agent."

**If it goes wrong:**

- A small local model may still try a tool call despite the instruction. That's fine — narrate it: "It reached for a tool; the trace shows exactly what it tried."

**Bridge to ep. 02:** "We passed a model string. Next: the two ways to specify a model, and where your system prompt actually lands."

## Slides & Diagrams

- `slides.md` — 3-slide Marp deck overview of the episode. Preview with the Marp VS Code extension or `npx @marp-team/marp-cli slides.md`
- `diagrams/` — Mermaid sources (`.mmd`) with rendered `.svg`/`.png`: architecture, virtual filesystem, context management, delegation, human-in-the-loop

## Run Instructions

```bash
cd deepagents_101/01-deepagent_intro
python 01-deepagent_intro.py

# Any other provider LangChain supports:
DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 01-deepagent_intro.py
```

## Environment Variables

| Variable           | Default             | Description                                                                             |
| ------------------ | ------------------- | --------------------------------------------------------------------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string (`openai:gpt-4.1-mini`, `anthropic:claude-sonnet-4-6`, …) |

Provider keys go in the repo-root `.env` — every script calls `load_dotenv()`. Setup (env + deps) is in the [series README](../README.md).
