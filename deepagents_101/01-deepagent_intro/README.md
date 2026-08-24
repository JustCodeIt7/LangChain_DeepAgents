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

## Run Instructions
```bash
cd deepagents_101/01-deepagent_intro
python 01-deepagent_intro.py

# Any other provider LangChain supports:
DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 01-deepagent_intro.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string (`openai:gpt-4.1-mini`, `anthropic:claude-sonnet-4-6`, …) |

Provider keys go in the repo-root `.env` — every script calls `load_dotenv()`. Setup (env + deps) is in the [series README](../README.md).
