# 15 — Long-Term Memory Across Conversations

## Overview
**Goal:** Make knowledge outlive a single conversation: episode 12's checkpointer remembers ONE thread; a store remembers ALL of them.

## What You'll Learn
- **`StoreBackend`**: a persistent key-value store the agent can read/write as files
- **`namespace` is a callable** receiving the run's `Runtime` — real deployments scope memory per user (e.g. `lambda rt: (rt.server_info.user.identity,)`); locally the episode pins one bucket
- **Mounting with `CompositeBackend`**: `/memories/` → store (persistent), everything else → `StateBackend` (disappears after the run)
- **`memory=[...]`**: loads those files into the system prompt at the start of every run

## Key Concepts
1. The episode proves it: thread `monday` teaches the agent "I'm vegetarian"; a brand-new thread `friday` (no shared history) still recalls it — from the memory file, not the conversation
2. `InMemoryStore` is the dev store; swap in a Postgres-backed store for production
3. Inspect what was stored with `store.search(("demo-user",))`

## Run Instructions
```bash
cd deepagents_101/15-long_term_memory
python 15-long_term_memory.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 15-long_term_memory.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
