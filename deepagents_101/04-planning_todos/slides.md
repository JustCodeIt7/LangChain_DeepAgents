---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 04 — Planning with Todos

*In 0.7 planning is opt-in: add the middleware, get the `write_todos` tool*

---

# Opt In to Planning

```python
from langchain.agents.middleware import TodoListMiddleware

agent = create_deep_agent(model=MODEL, middleware=[TodoListMiddleware()])
```

- Without the middleware there is **no `write_todos` tool at all**
- 0.6 had it on by default; **0.7 made it explicit** so simple agents stay lean
- The plan lives in state under the **`todos`** key — a list of `{content, status}`

---

# Watch the Plan Evolve

```python
for chunk in agent.stream({"messages": [...]}, stream_mode="updates"):
    for node_name, update in chunk.items():
        if "todos" in update: ...
```

- `stream_mode="updates"` yields **one chunk per node that just ran** — no waiting for the end
- Statuses cycle `pending` ○ → `in_progress` ◐ → `completed` ●
- Give it work worth planning: **three distinct steps** is the sweet spot

**Next (ep. 05):** the filesystem every agent already has — and it isn't on your disk.
