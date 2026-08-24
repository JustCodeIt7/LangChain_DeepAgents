# Episode 5 — Running Commands: the Shell Tool (and why it's dangerous)

## Overview

**Length:** ~20 minutes  
**Goal:** Give the agent the ability to execute shell commands within its workspace, with proper output capture and truncation. End on a cliffhanger about safety.

## What You'll Learn

- **Custom `@tool` for shell execution**: Writing `run_shell(command)` that runs subprocesses with cwd confined to the workspace
- **Output management**: Capturing stdout, stderr, and exit code; truncating long output to avoid context window overflow
- **Security awareness**: Why confining CWD is NOT sufficient — the agent can still run destructive commands like `rm -rf`

## Key Concepts

1. There is NO built-in shell tool in FilesystemBackend — you must write a custom `@tool` using Python's `subprocess` module
2. The shell tool sets `cwd=CODEIT_WORKDIR`, but this only changes the working directory, not what commands can do — `rm -rf /` would still attempt system deletion if permissions allow
3. Output truncation is critical: long command output (e.g., from `find /`) can exhaust the context window; always cap and summarize
4. **Never run unsandboxed on a real repository** — this episode demonstrates the danger, not safe practices

## Run Instructions

```bash
# Create workspace if needed:
mkdir -p ./workspace

# Ask the agent to install dependencies and run tests:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 05-shell-tool.py "Install fastapi and uvicorn with pip, then list installed packages."

# Or with OpenAI:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 05-shell-tool.py "Check the Python version and list files in /tmp."
```

## Prerequisites

```bash
pip install deepagents langchain-ollama rich python-dotenv
```
