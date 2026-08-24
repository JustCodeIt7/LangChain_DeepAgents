# 02 — Models and System Prompts

## Overview
**Goal:** See the two ways to specify a model and understand exactly where your `system_prompt` lands in the final prompt.

## What You'll Learn
- **Model as a string**: `"provider:model"` is handed to `init_chat_model`, so any LangChain provider works (`ollama:`, `openai:`, `anthropic:`, `google_genai:`)
- **Model as an instance**: build it yourself with `init_chat_model(MODEL, temperature=0)` when you need to tune parameters (temperature, max_tokens, timeouts, base_url)
- **Prompt composition**: your `system_prompt` does NOT replace the deep-agent instructions — it is placed FIRST, and the framework's tool guidance is appended after it (which is why the agent still knows how to use `write_file`, `task`, etc.)
- **`debug=True`**: prints every graph step — use it while developing, keep the question tiny

## Key Concepts
1. String = simplest; instance = full control. deepagents uses the instance as-is
2. The system prompt steers *personality and behavior*; tool knowledge comes from the framework
3. `debug=True` is a LangGraph trace — verbose by design

## Run Instructions
```bash
cd deepagents_101/02-models_and_prompts
python 02-models_and_prompts.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 02-models_and_prompts.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
