# 08 — Mixing Backends

## Overview
**Goal:** Route different paths to different backends in ONE agent — virtual scratch space plus a real directory, using `CompositeBackend`.

## What You'll Learn
- **`CompositeBackend(default=..., routes={...})`**: `default` handles everything; `routes` overrides by path prefix
- **Longest matching prefix wins**: `/disk/...` → real files under `./workspace`; everything else → virtual state files
- **One toolset, two storages**: the agent uses the same `write_file`/`read_file` for both sides — only the path prefix differs
- **Proving the split**: the virtual file appears only in `result["files"]`; the `/disk/` file is a genuine file readable with plain Python

## Key Concepts
1. Think of `routes` as mount points: `/disk/` is mounted on the real filesystem, the rest of the path space is memory
2. This is the pattern for "scratch work in memory, deliverables on disk"
3. The episode moves data across the boundary: write to `/scratch/`, read it back, copy to `/disk/`

## Run Instructions
```bash
cd deepagents_101/08-composite_backend
python 08-composite_backend.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 08-composite_backend.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).

## Notes
- Writes to `./workspace` inside this episode folder (git-ignored); stale files there are cleaned up at start.
