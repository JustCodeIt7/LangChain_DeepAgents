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

## Teaching Notes

**Hook:** "`FilesystemPermission` rules control what the agent may read and write — first match wins."

**Walk the cells:**

- **Step 2 — Seed something worth protecting:** A fake API key under `/secrets/`.
- **Step 3 — Write the rules:** Absolute paths, `**` for recursive, unmatched = allowed, order matters (specific first).
- **Step 4 — Read the protected file:** Allowed — the rule only covers `write`.
- **Step 5 — Write to it:** Denied before it runs.
- **Step 6 — Write elsewhere:** Still works.
- **Step 7 — The third mode:** `mode="interrupt"` — pauses for a human (the ep. 13 flow).

**On camera:**

- The three-part contrast (read OK / write denied / write elsewhere OK) is the structure. The "HACKED" overwrite attempt is a fun moment — show the denial.

**If it goes wrong:**

- The agent may report the denial in different words. The script prints the raw `ToolMessage` so you can see the actual error.

**Bridge to ep. 15:** "Permissions gate the filesystem. What about memory that outlives the conversation? Next: long-term memory."

## Run Instructions

```bash
cd deepagents_101/14-permissions
python 14-permissions.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 14-permissions.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
