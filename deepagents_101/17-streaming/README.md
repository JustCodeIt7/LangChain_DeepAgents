# 17 — Streaming

## Overview
**Goal:** Stream an agent run two ways — step-by-step progress (`updates`) and token-by-token output (`messages`) — and learn the shape of each.

## What You'll Learn
- **`stream_mode="updates"`**: one chunk per graph step, shaped `{node_name: state_update}` — what you render as "Thinking…", "Calling add…", "Done" in a progress UI
- **`stream_mode="messages"`**: tokens as the model produces them — for chat UIs
- **The most common streaming bug**: `messages` mode yields `(message_chunk, metadata)` TUPLES, not plain chunks — unpacking it wrong breaks everything
- **Filtering**: `messages` mode emits EVERY message including tool results; keep only `AIMessageChunk`s and drop internal machinery like `lc_source == "summarization"`
- **`subgraphs=True`**: also surfaces what SUBAGENTS are doing (each chunk arrives as `(namespace_tuple, chunk)`)

## Key Concepts
1. `updates` = progress indicator; `messages` = live answer text
2. Content can be a string (Ollama) or a list of blocks (OpenAI) — normalize before printing
3. Combine with episode 09's subagents to show each delegated task progressing independently

## Teaching Notes

**Hook:** "Two streaming modes: `updates` for progress UIs, `messages` for chat UIs."

**Walk the cells:**
- **Step 2 — A tool to watch:** `add`, so there's something to see besides text.
- **Step 3 — Mode 1, "updates":** One chunk per graph step, shaped `{node_name: state_update}`. This is what you render as "Thinking…", "Calling add…", "Done".
- **Step 4 — Mode 2, "messages":** Tokens as the model produces them. NOTE the shape: it yields `(message_chunk, metadata)` TUPLES — unpacking it wrong is the most common streaming bug. Filter to `AIMessageChunk` and drop summarization internals.
- **Step 5 — subgraphs=True:** Also surfaces what subagents are doing.

**On camera:**
- Run `updates` first (fast, discrete), then `messages` (live tokens) — the contrast is the lesson.

**If it goes wrong:**
- "too many values to unpack" = you're in `messages` mode and treating chunks as plain dicts. Point at the tuple unpacking.

**Bridge to ep. 18:** "Streaming shows the work. But long conversations grow — next keeps them small."

## Run Instructions
```bash
cd deepagents_101/17-streaming
python 17-streaming.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 17-streaming.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
