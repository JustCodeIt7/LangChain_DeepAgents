# 13 — Human in the Loop (Approvals)

## Overview
**Goal:** Pause the agent BEFORE a risky tool runs, inspect what it wants to do, and resume with a human decision.

## What You'll Learn
- **`interrupt_on={"send_email": True}`**: gates a tool behind human approval; `True` allows all four decision types, or pass an `InterruptOnConfig` dict such as `{"allowed_decisions": ["approve", "reject"]}`
- **The pause**: the run stops and returns `result["__interrupt__"]` describing the pending action
- **The resume**: `Command(resume={"decisions": [...]})` carries the decision back in
- **All four decision types**: `approve` (run as-is), `reject` (skip + message back to the model), `edit` (run with arguments YOU supply), `respond` (skip and feed your own text as the tool result)

## Key Concepts
1. **Requires a checkpointer** — the paused run has to be stored somewhere (`InMemorySaver()` here)
2. The same thread_id must be used on resume so the checkpointer finds the paused state
3. This is the mechanism behind approval gates in every "agent with permissions" product

## Run Instructions
```bash
cd deepagents_101/13-human_in_the_loop
python 13-human_in_the_loop.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 13-human_in_the_loop.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).

## Notes
- The script demonstrates `approve` and `reject` live; the `edit` and `respond` payloads are shown in Step 7 of the source.
