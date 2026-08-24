# Episode 4 — Writing Code: `write_file` + the Workspace Sandbox

## Overview

**Length:** ~10 minutes  
**Goal:** Demonstrate that the agent can create real files in its sandboxed workspace using the built-in `write_file` tool, and introduce a reusable helper for path resolution.

## What You'll Learn

- **`write_file`**: The FilesystemBackend's built-in file creation tool — no custom code needed
- **Sandbox reinforcement**: How `virtual_mode=True` ensures all writes stay within `CODEIT_WORKDIR`
- **`resolve_in_workspace(path)`**: A shared helper that resolves any path relative to the workspace root, used by tools in later episodes (shell, edit wrapper, repo map)

## Key Concepts

1. The agent can write real files using the built-in `write_file` tool — no custom implementation required
2. All writes are confined to the sandbox; the agent cannot escape `CODEIT_WORKDIR`
3. `resolve_in_workspace()` is a utility that normalizes and validates paths, ensuring they stay within bounds — it becomes a building block for subsequent episodes

## Run Instructions

```bash
# Create workspace if needed:
mkdir -p ./workspace

# Ask the agent to create a file:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 04-write-sandbox.py "Create main.py with a FastAPI app: GET /hello returns {'msg':'hello'}."

# Verify the file was created:
cat ./workspace/main.py
```

## Prerequisites

```bash
pip install deepagents langchain-ollama rich python-dotenv
```
