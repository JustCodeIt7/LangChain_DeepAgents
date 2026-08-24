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

## Teaching Notes

**Hook:** "The `execute` tool only exists when the backend can run a shell — and there is NO sandbox."

**Walk the cells:**

- **Step 2 — The negative demo first:** Ask the virtual agent to run `echo hi`. It can't — the tool isn't offered at all. That's the safe default, and proving it is the point.
- **Step 4 — Build a shell backend:** `LocalShellBackend(root_dir, timeout=30, inherit_env=False)`. `inherit_env=False` keeps your secrets out of the subprocess.
- **Step 5 — One explicit, safe command:** Be specific about the command. Say out loud: this runs with your user's permissions.
- **Step 6 — Verify the side effect:** Read `greeting.txt` back from real disk.

**On camera:**

- The before/after contrast (no execute → execute) is the teaching structure. Show the `$ echo ...` line in the output.

**If it goes wrong:**

- This runs real commands. Never feed untrusted input to this agent — whatever it decides to run WILL run.

**Bridge to ep. 08:** "One backend, one place. What if I want some paths virtual and some real? Next: mixing backends."

## Run Instructions

```bash
cd deepagents_101/07-shell_execute
python 07-shell_execute.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 07-shell_execute.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).

## Notes

- Runs **real shell commands** on your machine (scoped to `./workspace`, git-ignored).
