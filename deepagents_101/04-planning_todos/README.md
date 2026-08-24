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

## Run Instructions
```bash
cd deepagents_101/04-planning_todos
python 04-planning_todos.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 04-planning_todos.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
