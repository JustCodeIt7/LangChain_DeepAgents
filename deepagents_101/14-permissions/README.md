# 14 — Filesystem Permissions

## Overview
**Goal:** Control what the agent may read and write with `FilesystemPermission` rules — allow, deny, and interrupt.

## What You'll Learn
- **Rule shape**: `FilesystemPermission(operations=["write"], paths=["/secrets/**"], mode="deny")`
- **First match wins**: rules are evaluated in order, so list them specific → general
- **Unmatched paths are ALLOWED**: you only write the restrictions
- **Three modes**: `allow`, `deny`, and `interrupt` (pause for a human — the episode 13 `__interrupt__` / `Command(resume=...)` flow)

## Key Concepts
1. Every path must be absolute (start with `/`); use `**` to match recursively
2. `operations` scopes a rule — a `write`-only deny leaves reads untouched (the episode proves all three cases: read allowed, write denied, write elsewhere allowed)
3. `mode="interrupt"` is for paths that are risky but sometimes legitimate

## Run Instructions
```bash
cd deepagents_101/14-permissions
python 14-permissions.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 14-permissions.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
