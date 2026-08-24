---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 06 — Working on Real Files

*Swap the backend and the same tools now edit files that outlive the run*

---

# Scope It, Then Point At It

```python
from deepagents.backends import FilesystemBackend

backend = FilesystemBackend(root_dir=str(WORKSPACE), virtual_mode=True)
agent = create_deep_agent(model=MODEL, backend=backend)
```

- **`root_dir`** scopes the agent — always a directory you are happy for it to modify
- **`virtual_mode=True`** (default) sandboxes paths inside `root_dir`: no `../`, no `~/`
- Nothing else about the agent changes — same `read_file` / `write_file` / `edit_file`

---

# Mind the Path Style

```python
"/shopping.md"           # ✅  root_dir already scopes it
"workspace/shopping.md"  # ❌  creates workspace/workspace/
```

- Agent paths are **relative to `root_dir`** — `/shopping.md` means `<root_dir>/shopping.md`
- Say it in the system prompt: *"Paths are relative to the workspace root"*
- The payoff: read the files back with plain Python — **the changes survive the run**

**Next (ep. 07):** a backend that can also run shell commands — and why that is opt-in.
