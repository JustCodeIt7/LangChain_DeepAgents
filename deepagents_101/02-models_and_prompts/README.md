# 02 — Models and System Prompts

## Overview

**Goal:** See the two ways to specify a model and understand exactly where your `system_prompt` lands in the final prompt.

## What You'll Learn

- **Model as a string**: `"provider:model"` is handed to `init_chat_model`, so any LangChain provider works (`ollama:`, `openai:`, `anthropic:`, `google_genai:`)
- **Model as an instance**: build it yourself with `init_chat_model(MODEL, temperature=0)` when you need to tune parameters (temperature, max_tokens, timeouts, base_url)
- **Prompt composition**: your `system_prompt` does NOT replace the deep-agent instructions — it is placed FIRST, and the framework's tool guidance is appended after it (which is why the agent still knows how to use `write_file`, `task`, etc.)
- **Tracing the graph**: `debug=True` dumps raw state updates; `stream_mode="updates"` + a small formatter gives a readable step-by-step trace

## Key Concepts

1. String = simplest; instance = full control. deepagents uses the instance as-is
2. The system prompt steers _personality and behavior_; tool knowledge comes from the framework
3. `debug=True` dumps raw state; `stream_mode="updates"` gives a readable step-by-step trace

## Teaching Notes

**Hook:** "Two ways to give the agent a brain — and a surprise about where your system prompt lands."

**Walk the cells:**

- **Step 2 — A. model as a string:** `create_deep_agent(model=MODEL)`. deepagents hands the string to `init_chat_model`, so any LangChain provider works. Run it, show the answer.
- **Step 3 — B. model as an instance:** `init_chat_model(MODEL, temperature=0)`. Use this when you need to tune parameters (temperature, max_tokens, base_url). Run the same question — same behavior, more control.
- **Step 4 — C. custom system_prompt:** The pirate. This is the memorable moment — let it land. Then the key teaching point: your prompt is placed FIRST and the framework's tool guidance is appended AFTER it. The agent is still a full deep agent, just a pirate one.
- **Step 5 — D. tracing the graph:** `stream_mode="updates"` + a small `trace()` formatter. Each step shows the node, its messages, tool calls, and token counts. Keep the question tiny ("say ready").

**On camera:**

- Run A and B back to back with the same question to show they behave identically.
- The pirate answer is your clip — pause on it.

**If it goes wrong:**

- If the trace looks long, frame it: "This is every graph step — which node ran, what it produced, and how many tokens it used. It's how you debug."

**Bridge to ep. 03:** "So far the agent only has built-in tools. Next: add your own — a tool is just a Python function with a docstring."

## Slides & Diagrams

- `slides.md` — 3-slide Marp deck overview of the episode. Preview with the Marp VS Code extension or `npx @marp-team/marp-cli slides.md`
- `diagrams/` — Mermaid sources (`.mmd`) with rendered `.svg`/`.png`: model options, prompt composition, debug trace, provider profiles

## Run Instructions

```bash
cd deepagents_101/02-models_and_prompts
python 02-models_and_prompts.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 02-models_and_prompts.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
