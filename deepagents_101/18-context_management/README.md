# 18 — Context Management (Summarization)

## Overview
**Goal:** Watch `SummarizationMiddleware` compress old turns into a summary automatically — forced early here so you can see it happen cheaply.

## What You'll Learn
- **`SummarizationMiddleware(trigger=..., keep=...)`**: `trigger=("messages", 4)` = summarize once history exceeds 4 messages; `keep=("messages", 2)` = keep the 2 newest verbatim
- **Replacing the built-in**: because the custom instance's `.name` matches the built-in (`"SummarizationMiddleware"`), deepagents REPLACES the default instead of stacking a second one
- **Default behavior**: every deep agent already summarizes automatically, but only near the model's context limit (~85%) — impossible to demo cheaply
- **The other half of context management**: tool results over ~20k tokens are automatically offloaded to a file in the backend, replaced with a short preview + path the agent can `read_file` back on demand

## Key Concepts
1. **Compression is not amnesia**: details from the early, summarized turns should still be answerable — fewer tokens, same knowledge
2. The episode tracks the message count after each turn to show the history shrinking
3. A checkpointer + `thread_id` is needed so the conversation persists across turns

## Run Instructions
```bash
cd deepagents_101/18-context_management
python 18-context_management.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 18-context_management.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
