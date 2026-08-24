---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 07 — Running Shell Commands

*The `execute` tool only exists when the backend can actually run a shell*

---

# The Tool Is Earned, Not Given

```python
create_deep_agent(model=MODEL, backend=StateBackend())      # no execute tool
create_deep_agent(model=MODEL, backend=LocalShellBackend(...))  # execute attached
```

- On a virtual backend `execute` is **never offered to the model** — a safe default
- `LocalShellBackend` = `FilesystemBackend` **+** real subprocess execution
- Ask a `StateBackend` agent to run a command and you can count zero `execute` calls

---

# Configure It, and Respect It

```python
LocalShellBackend(root_dir=str(WORKSPACE), timeout=30, inherit_env=False)
```

- **`timeout`** caps a single command · **`inherit_env=False`** keeps your secrets out of the subprocess
- ⚠️ **There is no sandbox.** Whatever it decides to run *will* run as your user
- Never let untrusted input reach a shell-capable agent

**Next (ep. 08):** one agent, several backends — route paths with `CompositeBackend`.
