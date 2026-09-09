---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 15 — Long-Term Memory

*A checkpointer remembers one thread; a store remembers all of them*

---

# Mount a Store at `/memories/`

```python
store = InMemoryStore()
memory_backend = StoreBackend(store=store, namespace=lambda runtime: ("demo-user",))

backend = CompositeBackend(default=StateBackend(), routes={"/memories/": memory_backend})
```

- `namespace` is a **callable** receiving the run's `Runtime` — scope memory per user in production,
  e.g. `lambda rt: (rt.server_info.user.identity,)`
- Everything outside `/memories/` stays virtual and disappears when the run ends

---

# Load It Every Run

```python
agent = create_deep_agent(model=MODEL, backend=backend, memory=["/memories/preferences.md"])
```

- `memory=[...]` reads those files into the **system prompt at the start of every run**
- Teach it on thread `monday`; ask on thread `friday` — **no shared message history**,
  so anything it recalls came from the file
- Inspect what landed: `store.search(("demo-user",))`

**Next (ep. 16):** packaging expertise as skills the agent loads only when relevant.
