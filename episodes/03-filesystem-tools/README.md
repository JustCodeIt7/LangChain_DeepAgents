# Episode 3 — Filesystem Sandbox: Safe Code Exploration

## Overview

**Length:** ~18 minutes  
**Goal:** Attach a `FilesystemBackend` to the agent, giving it built-in file operations (ls, read, write, edit, glob, grep) confined to a sandboxed workspace directory.

## What You'll Learn

- **FilesystemBackend**: The Deep Agents backend that provides automatic filesystem tools when attached
- **`virtual_mode=True`**: Sandbox discipline — all paths resolve within `CODEIT_WORKDIR`, preventing the agent from touching files outside its designated area
- **Custom tool composition**: Writing a domain-specific `@tool` (`read_summary`) that wraps built-in capabilities with custom behavior (truncation policy)
- **Workspace isolation**: How to configure and validate the working directory before the agent starts

## Key Concepts

1. `FilesystemBackend(workdir=..., virtual_mode=True)` injects ls/read_file/write_file/edit_file/glob/grep as tools — no manual registration needed
2. The sandbox confines all file operations to a single root; paths outside are rejected or rewritten
3. Custom `@tool` functions can coexist with backend-provided tools, adding domain-specific logic (e.g., truncation, formatting) while delegating the actual I/O
4. `CODEIT_WORKDIR` environment variable sets the workspace root — set it before running

## Run Instructions

```bash
# Create a workspace directory first:
mkdir -p ./workspace && echo "# My Project" > ./workspace/README.md

# Run with Ollama:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 03-filesystem-tools.py "List the files in this project and summarize README.md."

# Or with OpenAI:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 03-filesystem-tools.py "List the files in this project and summarize README.md."
```

## Prerequisites

```bash
pip install deepagents langchain-ollama rich python-dotenv
```
