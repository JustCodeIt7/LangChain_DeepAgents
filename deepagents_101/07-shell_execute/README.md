# 07 — Running Shell Commands

## Overview
**Goal:** Give the agent a real shell with `LocalShellBackend` — and first confirm the safe default: the `execute` tool is not offered at all without a shell-capable backend.

## What You'll Learn
- **`execute` is backend-gated**: on the default `StateBackend` the tool is simply not offered to the model — a safe default the episode demonstrates explicitly
- **`LocalShellBackend`** = `FilesystemBackend` + real subprocess execution
- **Safety knobs**: `timeout` caps how long a single command may run; `inherit_env=False` (the default) keeps your secrets out of the subprocess
- **Verifying side effects**: the episode runs `echo ... > greeting.txt` and reads the file back with plain Python

## Key Concepts
1. **There is NO sandbox** — whatever the agent decides to run WILL run with your user's permissions
2. Be specific about the command in the prompt; never let untrusted input reach this agent
3. The episode prints every `execute` tool call so you can see exactly what ran

## Run Instructions
```bash
cd deepagents_101/07-shell_execute
python 07-shell_execute.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 07-shell_execute.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).

## Notes
- Runs **real shell commands** on your machine (scoped to `./workspace`, git-ignored).
