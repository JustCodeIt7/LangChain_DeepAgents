# 05 — The Virtual Filesystem

## Overview

**Goal:** Seed files into the agent's default in-memory filesystem, let it edit them, and read the result back out of the state.

## What You'll Learn

- **`StateBackend` is the default**: every deep agent has a filesystem; by default it is virtual and lives in graph state — nothing touches your real disk
- **Seeding with `create_file_data()`**: builds the `FileData` entry (content + timestamps/encoding) so you don't hand-roll the shape
- **Seed files go in the INVOKE INPUT**, not the constructor: `agent.invoke({"messages": [...], "files": seed_files})`
- **Reading back**: the modified filesystem comes back under `result["files"]` — same shape as the seed

## Key Concepts

1. `files` is a dict of `path -> FileData`; paths are absolute (`/notes/todo.md`)
2. The agent uses the same `ls`/`read_file`/`edit_file` tools it would use on a real backend — only the storage differs
3. Perfect for safe experimentation: the whole filesystem disappears when the process exits

## Teaching Notes

**Hook:** "Every deep agent has a filesystem. By default it's virtual — nothing touches your disk."

**Walk the cells:**

- **Step 2 — Seed files:** `files` is a dict of path → FileData; `create_file_data()` builds the entry so you don't hand-roll the shape.
- **Step 3 — Build the agent:** `StateBackend()` is the default — passing it explicitly just makes it visible.
- **Step 4 — Run (the gotcha):** The seed files go in the INVOKE INPUT, not the constructor — `agent.invoke({"messages": [...], "files": seed_files})`. The agent reads state.
- **Step 5 — Which tools did it use:** Show the `ls`/`read_file`/`edit_file` calls.
- **Step 6 — Read it back:** The modified file comes back under `result["files"]` — same shape as the seed.

**On camera:**

- Show `/notes/todo.md` before and after — the appended line is the proof it worked.

**If it goes wrong:**

- The model may `write_file` (overwrite) instead of `edit_file` (append). The demo still works; the content just differs.

**Bridge to ep. 06:** "Virtual is safe but ephemeral — it vanishes when the process exits. Next: real files on disk."

## Slides & Diagrams

- `slides.md` — 3-slide Marp deck overview of the episode. Preview with the Marp VS Code extension or `npx @marp-team/marp-cli slides.md`
- `diagrams/` — Mermaid sources (`.mmd`) with rendered `.svg`/`.png`: state backend, backend choice, file lifecycle

## Run Instructions

```bash
cd deepagents_101/05-virtual_filesystem
python 05-virtual_filesystem.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 05-virtual_filesystem.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
