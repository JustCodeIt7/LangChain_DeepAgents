# Episode 7 — The System Prompt: Engineering Personality & Rules

## Overview
**Length:** ~22 minutes  
**Goal:** Give the agent a real system prompt with personality, tool-use policies, safety rules, and editing conventions. Load project-specific context from `AGENTS.md` or `CODEIT.md`.

## What You'll Learn
- **System prompt composition**: How to write an effective system prompt that guides behavior without overriding built-in tool descriptions
- **`AGENTS.md` / `CODEIT.md`**: Loading project-specific instructions from the workspace root and composing them with your base system prompt
- **Middleware injection**: Understanding how Deep Agents' middleware injects its own tool descriptions on top of your system prompt — you ADD policy, not replace it

## Key Concepts
1. The system prompt is your primary lever for shaping agent behavior: tone, safety rules, coding conventions, and workflow policies all live here
2. `AGENTS.md` (Deep Agents' convention) or `CODEIT.md` provides project-specific context — the agent reads these at startup to understand the codebase it's working in
3. Deep Agents middleware automatically injects tool descriptions into the system prompt; your custom instructions are layered on top, not replacing them
4. A well-crafted system prompt reduces hallucination and keeps the agent focused on the task

## Run Instructions
```bash
# Create workspace with an AGENTS.md:
mkdir -p ./workspace
echo "# My Project\nUse FastAPI conventions. The bug is in main.py." > ./workspace/AGENTS.md

# Ask about the project context:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 07-system-prompt.py "What is this project? What coding style should I use?"

# Or with OpenAI:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 07-system-prompt.py "Summarize the project conventions."
```

## Prerequisites
```bash
pip install deepagents langchain-ollama rich python-dotenv
```