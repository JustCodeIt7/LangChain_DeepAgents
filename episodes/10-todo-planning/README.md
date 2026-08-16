# Episode 10 — Planning: TodoList & Task Decomposition

## Overview
**Length:** ~30 minutes  
**Goal:** Teach the agent to plan before acting by making task decomposition explicit through a todo list system.

## What You'll Learn
- **`TodoListMiddleware`**: Deep Agents' built-in middleware (#1 in the default stack) that provides persistent, structured task tracking across conversation turns
- **Explicit planning tools**: `plan(steps)` and `complete_todo(id)` — custom `@tool` functions that instruct the model to write todos via the built-in todo system
- **`render_todos(state)`**: A CLI helper (not a tool) that displays the current todo list state in a readable format

## Key Concepts
1. Planning before acting reduces wasted effort: the agent breaks down complex tasks into discrete, trackable steps instead of diving in blindly
2. `TodoListMiddleware` is always present — the `write_todos` tool is automatically available; you don't need to register it yourself
3. Custom planning tools (`plan`, `complete_todo`) work by instructing the model to call `write_todos` with specific items — tools can't call other tools directly, so the model orchestrates the flow
4. State key may be `todos` or `todo_list` depending on version — always check both for compatibility

## Run Instructions
```bash
# Create workspace if needed:
mkdir -p ./workspace

# Ask the agent to plan before executing:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 10-todo-planning.py "Add basic auth to a FastAPI app. Plan 4 steps first."

# Or with OpenAI (recommended for planning reliability):
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key LLM_MODEL=gpt-4o \
    python 10-todo-planning.py "Add basic auth to a FastAPI app. Plan 4 steps first."

# ⚠️ Planning is unreliable on models ≤8B — use qwen2.5-coder:32b or OpenAI.
```

## Prerequisites
```bash
pip install deepagents langchain-ollama rich python-dotenv
```