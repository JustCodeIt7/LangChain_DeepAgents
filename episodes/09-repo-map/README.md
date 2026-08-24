# Episode 9 — Context Management: Repo Map & Token Trimming

## Overview

**Length:** ~28 minutes  
**Goal:** Give the agent a bird's-eye view of the codebase without reading every file, and manage context window usage with token estimation and history trimming.

## What You'll Learn

- **`build_repo_map(root)`**: Walks the workspace directory tree, uses Python's `ast` module to extract top-level function/class signatures, and returns a compact text map — no full file reads needed
- **`estimate_tokens(text)`**: A ~4 chars/token heuristic for budgeting context window usage
- **`trim_history(messages, max_tokens)`**: Drops oldest conversation turns to fit within a token cap

## Key Concepts

1. Reading every file in a large codebase is expensive and slow; a repo map provides structural overview (function/class names + signatures) at a fraction of the cost
2. Python's `ast` module parses source files into an abstract syntax tree — you can extract definitions without executing or fully reading the code
3. Token estimation helps you decide when to trim conversation history: if total tokens exceed your model's context window, drop older turns that are no longer relevant
4. Deep Agents' FilesystemMiddleware already does internal context engineering; this episode adds a teaching layer for custom control and understanding

## Run Instructions

```bash
# Create workspace with some Python files:
mkdir -p ./workspace/src
echo "def greet(name):\n    return f'Hello, {name}'" > ./workspace/src/main.py
echo "# Project docs\nThis is a demo project." > ./workspace/README.md

# Ask the agent to map and explore:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 09-repo-map.py "Where is greet defined? Use build_repo_map first, then read the file."

# Or with OpenAI:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 09-repo-map.py "Show me the structure of this codebase."
```

## Prerequisites

```bash
pip install deepagents langchain-ollama rich python-dotenv
```
