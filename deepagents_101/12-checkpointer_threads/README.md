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

## Teaching Notes

**Hook:** "A checkpointer saves state after every step — so turn 2 remembers turn 1."

**Walk the cells:**

- **Step 2 — Add a checkpointer:** `checkpointer=InMemorySaver()`. Dev store (RAM); swap in SqliteSaver/PostgresSaver to survive a restart.
- **Step 3 — Two turns on the SAME thread:** The second invoke passes no history — the checkpointer reloads it from thread "alice". This is what makes a real chat loop possible.
- **Step 4 — Same question, DIFFERENT thread:** Thread "bob" has its own (empty) history — the agent has no idea.
- **Step 5 — Inspect the stored history:** `get_state()` reads back what the checkpointer holds per thread.

**On camera:**

- The alice/bob contrast is the whole episode — alice remembers 42, bob doesn't. Let both answers land.

**If it goes wrong:**

- This demo is deterministic; the main risk is a model that rambles. Keep the "one short sentence" prompt.

**Bridge to ep. 13:** "Memory is great — but what if the agent wants to do something risky? Next: human in the loop."

## Run Instructions

```bash
cd deepagents_101/12-checkpointer_threads
python 12-checkpointer_threads.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 12-checkpointer_threads.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
