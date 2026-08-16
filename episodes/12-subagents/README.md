# Episode 12 — Sub-Agents: Specialists in Isolated Context

## Overview
**Length:** ~35 minutes  
**Goal:** Teach the agent to delegate work to specialized sub-agents that run with isolated context and return only a summary. Uses Deep Agents' built-in `SubAgentMiddleware`.

## What You'll Learn
- **`SubAgentMiddleware`**: The built-in middleware (#2 in the default stack) that enables sub-agent delegation via the `task` tool
- **Custom subagent specs**: Defining "explorer" (read-only: repo map + ls/read/grep, no shell/writes) and "tester" (run_tests + edit_file_safe, no shell/write_file) as isolated specialists
- **`spawn_subagent(task, agent)`**: Sugar over the built-in `task` tool that simplifies delegation

## Key Concepts
1. Subagents run with **isolated context** — they don't see the parent's full conversation history; only a summary returns to the parent
2. Each subagent has its own **tool set**: you define which tools are available, creating specialists (e.g., an explorer that can read but not write)
3. Subagents are **stateless** — give complete instructions in one task call; don't rely on prior context carrying over
4. Delegation requires a larger model (32b+ or OpenAI) — small models struggle to decide when and how to delegate effectively

## Run Instructions
```bash
# Create workspace with some files:
mkdir -p ./workspace/src && echo "def main():\n    pass" > ./workspace/src/app.py

# Ask the agent to use a subagent for exploration:
LLM_MODEL=qwen2.5-coder:32b CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 12-subagents.py "Use the explorer subagent to map this codebase."

# Or with OpenAI:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 12-subagents.py "Use the tester subagent to run tests and fix any failures."
```

## Prerequisites
```bash
pip install deepagents langchain-ollama rich python-dotenv
```