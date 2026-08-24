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

## Teaching Notes

**Hook:** "A tool is just a Python function with a docstring. Two ways to write one."

**Walk the cells:**

- **Step 2 — Plain function:** `word_count`. deepagents inspects the signature and docstring to build the schema. Stress: the docstring IS what the model reads — write it for the model. Keep param types simple (str/int/bool).
- **Step 3 — @tool decorator:** `reverse_text`. Same result, but explicit control (custom name, args schema, return_direct) and a real BaseTool object.
- **Step 4 — Hand both to the agent:** `tools=` is ADDITIVE — it never removes the built-ins. The system prompt says "do not use filesystem tools" to keep the demo focused.
- **Step 5 — A task needing BOTH tools:** Forces two separate tool calls.
- **Step 6 — Inspect:** Show the `tool_calls` on the AI messages, then the `ToolMessage` results.

**On camera:**

- The "Tool calls made" section is the payoff — show `reverse_text` then `word_count` firing in sequence.

**If it goes wrong:**

- A small model may answer without calling the tools (count the words in its head). The prompt says "use your tools for both steps." If it skips, that's a teaching moment about model size vs. instruction-following.

**Bridge to ep. 04:** "Tools are great, but multi-step work needs a plan. Next: the agent's to-do list."

## Slides & Diagrams

- `slides.md` — 3-slide Marp deck overview of the episode. Preview with the Marp VS Code extension or `npx @marp-team/marp-cli slides.md`
- `diagrams/` — Mermaid sources (`.mmd`) with rendered `.svg`/`.png`: tool definition, additive tools, tool call loop

## Run Instructions

```bash
cd deepagents_101/03-custom_tools
python 03-custom_tools.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 03-custom_tools.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
