---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 08 — Mixing Backends

*One agent, several filesystems — routed by path prefix*

---

# Routes Are Mount Points

```python
backend = CompositeBackend(
    default=StateBackend(),
    routes={"/disk/": FilesystemBackend(root_dir=str(WORKSPACE), virtual_mode=True)},
)
```

| Path | Backend | Survives the run? |
| --- | --- | --- |
| `/disk/...` | `FilesystemBackend` (real `./workspace`) | ✅ yes |
| everything else | `StateBackend` (virtual) | ❌ no |

- `default=` catches everything; `routes=` overrides by prefix — **longest match wins**

---

# One Tool Set, Two Destinations

```python
write_file("/scratch/note.md", ...)   # virtual — result["files"]
write_file("/disk/note.md", ...)      # real   — ./workspace/note.md
```

- The agent uses the **same `read_file` / `write_file`** for both — only the prefix differs
- That makes moving data across the boundary a normal read-then-write
- Prove it: virtual files show up in `result["files"]`, real ones open with plain Python

**Next (ep. 09):** delegation — the `task` tool and why subagents get their own context.
