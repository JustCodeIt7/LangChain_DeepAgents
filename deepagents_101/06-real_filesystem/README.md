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

## Run Instructions
```bash
cd deepagents_101/06-real_filesystem
python 06-real_filesystem.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 06-real_filesystem.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).

## Notes
- Writes to `./workspace` inside this episode folder (git-ignored).
