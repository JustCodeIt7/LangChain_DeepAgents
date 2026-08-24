# 03 — Adding Your Own Tools

## Overview
**Goal:** Add custom tools to a deep agent — as a plain function or with the `@tool` decorator — and watch the agent call them.

## What You'll Learn
- **Plain function tools**: deepagents inspects the signature and docstring to build the tool schema
- **`@tool` decorator**: same result, but explicit control (custom name, args schema, `return_direct`) and a real `BaseTool` object
- **Additive tools**: `tools=` ADDS to the built-in suite — it never removes `ls`/`read_file`/`task`/etc.
- **Inspecting the run**: reading `tool_calls` off AI messages and `ToolMessage` results from the final state

## Key Concepts
1. **The docstring IS the tool description the model reads** — write it for the model (what it does, what each arg is)
2. Keep parameter types simple (`str`/`int`/`bool`) — smaller models coerce them better
3. Tool results come back as `ToolMessage` objects in `result["messages"]`

## Run Instructions
```bash
cd deepagents_101/03-custom_tools
python 03-custom_tools.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 03-custom_tools.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
