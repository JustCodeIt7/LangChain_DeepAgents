# 03 — Adding Your Own Tools

## Overview

**Goal:** Add custom tools to a deep agent — as a plain function or with the `@tool` decorator — and watch the agent call them. Then push further: tools that return structured data, run async, or short-circuit with `return_direct`.

## What You'll Learn

- **Plain function tools**: deepagents inspects the signature and docstring to build the tool schema
- **`@tool` decorator**: same result, but explicit control (custom name, args schema, `return_direct`) and a real `BaseTool` object
- **Additive tools**: `tools=` ADDS to the built-in suite — it never removes `ls`/`read_file`/`task`/etc.
- **Inspecting the run**: reading `tool_calls` off AI messages and `ToolMessage` results from the final state
- **Structured returns**: a tool can return a `dict` (serialized to JSON) so the model reads specific fields
- **Async tools**: `async def` tools for I/O-bound work — the framework awaits them
- **`return_direct`**: a tool whose output is returned as the final answer with no extra LLM call

## Key Concepts

1. **The docstring IS the tool description the model reads** — write it for the model (what it does, what each arg is)
2. Keep parameter types simple (`str`/`int`/`bool`) — smaller models coerce them better
3. Tool results come back as `ToolMessage` objects in `result["messages"]`
4. A tool's return value is serialized into the `ToolMessage` — return a `dict` for structured data the model can read field-by-field
5. Tools can be `async def` (for I/O) and can set `return_direct=True` to skip the model's final turn

## Teaching Notes

**Hook:** "A tool is just a Python function with a docstring. Two ways to write one."

**Walk the cells:**

- **Step 2 — Plain function:** `word_count`. deepagents inspects the signature and docstring to build the schema. Stress: the docstring IS what the model reads — write it for the model. Keep param types simple (str/int/bool).
- **Step 3 — @tool decorator:** `reverse_text`. Same result, but explicit control (custom name, args schema, return_direct) and a real BaseTool object.
- **Step 4 — Hand both to the agent:** `tools=` is ADDITIVE — it never removes the built-ins. The system prompt says "do not use filesystem tools" to keep the demo focused.
- **Step 5 — A task needing BOTH tools:** Forces two separate tool calls.
- **Step 6 — Inspect:** Show the `tool_calls` on the AI messages, then the `ToolMessage` results.
- **Step 7 — Structured return:** `lookup_product` returns a `dict`; the model reads the fields (price, in_stock, category).
- **Step 8 — Async tool:** `fetch_quote` is `async def`; the model calls it like any sync tool, but the agent must run on the async path (`.ainvoke`) — an async-only tool raises on sync `.invoke()`.
- **Step 9 — return_direct:** `get_order_status` has `return_direct=True`; its output becomes the final answer with no extra LLM call.
- **Step 10 — Second agent:** a fresh agent with the three new tools, plus two helpers: `show_tool_calls` (inspect a run) and `run_task` (run a task on the async path, reusing one event loop — the Ollama async client binds its connection pool to a single loop, so `asyncio.run()` per task breaks it).
- **Steps 11–13 — One task per tool:** each task is worded to trigger exactly one tool; the "Try also" comments give extra test tasks to run on camera.

**On camera:**

- The "Tool calls made" section is the payoff — show `reverse_text` then `word_count` firing in sequence.
- For Task 3, the "Final answer" is byte-for-byte the tool's output — no model rephrasing. That's the `return_direct` payoff; point at it.

**If it goes wrong:**

- A small model may answer without calling the tools (count the words in its head). The prompt says "use your tools for both steps." If it skips, that's a teaching moment about model size vs. instruction-following.
- With three tools in one agent, a small model might pick the wrong one. The domains are deliberately distinct (product / stock / order) to keep it unambiguous. If it misfires, tighten the task wording or the system prompt.
- If you see `Event loop is closed` from the Ollama client, you're calling `asyncio.run()` once per task. Use the shared-loop `run_task` helper (one loop for all tasks) instead.

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
