# 04 — Planning with Todos

## Overview

**Goal:** Opt in to task planning with `TodoListMiddleware` and watch the agent's plan evolve live while it works.

## What You'll Learn

- **Planning is opt-in in deepagents 0.7**: add `middleware=[TodoListMiddleware()]` to get the `write_todos` tool (in 0.6 it was on by default; 0.7 made it explicit so simple agents stay lean)
- **Todos live in state**: once the tool is used, the plan appears under the `todos` key
- **Watching the plan**: `agent.stream(..., stream_mode="updates")` yields one chunk per node, so each `write_todos` revision is visible as it lands

## Key Concepts

1. Without the middleware there is no `write_todos` tool at all
2. Three distinct steps is the sweet spot for a demo task — enough to justify planning, small enough to stay fast
3. Smaller local models sometimes answer without planning — try a longer task or a larger model before assuming the code is wrong

## Teaching Notes

**Hook:** "In deepagents 0.7, planning is opt-in — one middleware line gives the agent a to-do list it updates as it works."

**Walk the cells:**

- **Step 2 — Opt in:** `middleware=[TodoListMiddleware()]`. Without it, the `write_todos` tool doesn't exist at all. Mention: on by default in 0.6, explicit in 0.7.
- **Step 3 — A task that deserves a plan:** Three distinct steps is the sweet spot — enough to justify planning, small enough to stay fast.
- **Step 4 — Stream the run:** `stream(stream_mode="updates")` yields one chunk per node, so each `write_todos` revision is visible as it lands.
- **Step 5 — Show the plan evolve:** The `○ ◐ ●` marks show pending → in-progress → completed.

**On camera:**

- "The plan was revised N times" is the money shot — the plan changes live while the agent works.

**If it goes wrong:**

- A small model may answer without planning. The script prints a yellow hint. Have a fallback line: "It skipped the plan — try a longer task or a larger model."

**Bridge to ep. 05:** "The agent can plan. Now give it a place to work — the filesystem."

## Run Instructions

```bash
cd deepagents_101/04-planning_todos
python 04-planning_todos.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 04-planning_todos.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
