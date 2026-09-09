---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 14 — Filesystem Permissions

*Declarative rules over paths — allow, deny, or ask a human*

---

# Write Only the Restrictions

```python
permissions = [
    FilesystemPermission(operations=["write"], paths=["/secrets/**"], mode="deny"),
]
agent = create_deep_agent(model=MODEL, backend=StateBackend(), permissions=permissions)
```

- Every path is **absolute**; `**` matches recursively
- Anything **no rule matches is allowed** — you only spell out what to restrict
- **First match wins**, so order rules specific → general

---

# Three Modes, One Demo

| Attempt | Matching rule | Outcome |
| --- | --- | --- |
| read `/secrets/api_key.md` | rule covers `write` only | ✅ allowed |
| write `/secrets/api_key.md` | `deny` on `/secrets/**` | ❌ refused before it runs |
| write `/notes/scratch.md` | no rule matches | ✅ allowed |

- `mode="allow"` · `mode="deny"` · **`mode="interrupt"`** — the third asks a human,
  using exactly the `__interrupt__` / `Command(resume=...)` flow from ep. 13

**Next (ep. 15):** memory that outlives the conversation, not just the thread.
