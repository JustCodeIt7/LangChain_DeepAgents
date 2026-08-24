# 12 — Memory Within a Conversation

## Overview
**Goal:** Make turn 2 remember turn 1 with a checkpointer, and see how `thread_id` isolates conversations.

## What You'll Learn
- **`checkpointer=InMemorySaver()`**: saves state after every step, so the second `invoke` needs no history — the checkpointer reloads it
- **`thread_id` names the conversation**: same id = same history; a different id is a completely separate conversation
- **`agent.get_state(config)`**: read back whatever the checkpointer holds for a thread
- **Why isolation matters**: one deployment can serve many users safely because threads never share history

## Key Concepts
1. The episode proves it: thread `alice` remembers "my favorite number is 42"; thread `bob` asked the same question has no idea
2. `InMemorySaver` keeps history in RAM — great for demos and tests; swap in `SqliteSaver` or `PostgresSaver` for something that survives a restart
3. This is what makes a real chat loop possible

## Run Instructions
```bash
cd deepagents_101/12-checkpointer_threads
python 12-checkpointer_threads.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 12-checkpointer_threads.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
