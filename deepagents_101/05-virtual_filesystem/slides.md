---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 05 — The Virtual Filesystem

*Every deep agent has a filesystem — by default it lives in graph state, not on your disk*

---

# Seed Files In

```python
from deepagents.backends import StateBackend
from deepagents.backends.utils import create_file_data

seed_files = {"/notes/todo.md": create_file_data("# Todo\n- [ ] buy milk\n")}

result = agent.invoke({"messages": [...], "files": seed_files})   # <- INVOKE input
```

- `StateBackend()` is the **default** — passing it explicitly just makes it visible
- `create_file_data()` builds the `FileData` entry (content + metadata) for you
- Files go in the **invoke input**, not the constructor — the agent reads state

---

# Read Files Back Out

```python
result["files"]["/notes/todo.md"]["content"]
```

- Same shape going in and coming out — `path -> FileData`
- The agent uses the ordinary `ls` / `read_file` / `edit_file` tools; only the **backend** differs
- Nothing touches real disk — perfect for safe experimentation and tests

**Next (ep. 06):** swap in `FilesystemBackend` and let the changes outlive the run.
