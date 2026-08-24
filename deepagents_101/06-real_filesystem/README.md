# 06 — Working on Real Files

## Overview
**Goal:** Swap the virtual backend for `FilesystemBackend` so the agent edits real files on disk — and prove the changes outlive the run.

## What You'll Learn
- **`FilesystemBackend(root_dir=...)`**: scopes the agent to a directory you are happy for it to modify
- **`virtual_mode=True`** (the default): sandboxes paths inside `root_dir`, so the agent cannot wander into `../` or `~/` even if it tries
- **Path style**: agent paths are relative to `root_dir` — `/shopping.md` means `<root_dir>/shopping.md`, NOT `workspace/shopping.md`
- **Verifying without the agent**: reading the files back with plain Python is the payoff of a real backend

## Key Concepts
1. Always scope a real-filesystem agent to a scratch directory (this episode uses `./workspace` next to the script)
2. Using the folder name again in a path would create `workspace/workspace/` — root_dir already scopes it
3. The same `ls`/`read_file`/`write_file`/`edit_file` tools work unchanged; only the backend differs

## Teaching Notes

**Hook:** "One line changes the backend, and the agent starts editing real files on your disk."

**Walk the cells:**
- **Step 2 — Prepare a scratch workspace:** Always scope a real-filesystem agent to a directory you're happy for it to modify. Here it's `./workspace` next to the script.
- **Step 3 — Point the backend at it:** `FilesystemBackend(root_dir=..., virtual_mode=True)`. `virtual_mode` blocks escapes like `../` or `~/`.
- **Step 4 — Ask it to touch real files:** Note the path style — `/shopping.md`, NOT `workspace/shopping.md`. root_dir already scopes it.
- **Step 5 — Prove it:** Read the files back with plain Python, no agent involved. The changes outlive the run.

**On camera:**
- Step 5 is the payoff — open the files in an editor (or `cat` them) to show they're real, persistent files.

**If it goes wrong:**
- If the agent writes to `workspace/shopping.md` it creates a nested `workspace/workspace/` folder. That's exactly what the path-style warning is for — narrate it if it happens.

**Bridge to ep. 07:** "Files are great. What about running commands? Next: a real shell."

## Run Instructions
```bash
cd deepagents_101/06-real_filesystem
python 06-real_filesystem.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 06-real_filesystem.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).

## Notes
- Writes to `./workspace` inside this episode folder (git-ignored).
