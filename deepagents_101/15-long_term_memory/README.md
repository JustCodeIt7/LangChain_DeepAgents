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

## Teaching Notes

**Hook:** "A checkpointer remembers ONE thread; a store remembers ALL of them."

**Walk the cells:**

- **Step 2 — A store + namespace:** `InMemoryStore` + `StoreBackend(namespace=lambda rt: ("demo-user",))`. The namespace is a callable, so real deployments can scope memory per user.
- **Step 3 — Mount at /memories/:** Everything else stays virtual. `memory=[MEMORY_FILE]` loads that file into the system prompt on every run.
- **Step 4 — Teach it something on thread "monday."**
- **Step 5 — Inspect the store:** The file is now outside any conversation history.
- **Step 6 — A brand-new thread "friday":** Recall comes from the memory file, not the conversation.

**On camera:**

- The friday recall is the payoff — the agent has never met this conversation but knows you're vegetarian.

**If it goes wrong:**

- The agent must actually write the file — the prompt says "save it to your memory file." If it doesn't, the friday recall fails. That's a teaching moment about making the save explicit.

**Bridge to ep. 16:** "Memory is files in a store. What if the expertise is a document the agent loads on demand? Next: skills."

## Slides & Diagrams

- `slides.md` — 3-slide Marp deck overview of the episode. Preview with the Marp VS Code extension or `npx @marp-team/marp-cli slides.md`
- `diagrams/` — Mermaid sources (`.mmd`) with rendered `.svg`/`.png`: memory layers, store mount, recall flow

## Run Instructions

```bash
cd deepagents_101/15-long_term_memory
python 15-long_term_memory.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 15-long_term_memory.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
