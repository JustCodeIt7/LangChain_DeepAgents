---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 13 — Human in the Loop

*Pause before a risky tool runs, decide, then resume*

---

# Gate the Tool

```python
agent = create_deep_agent(
    model=MODEL,
    tools=[send_email],
    interrupt_on={"send_email": True},
    checkpointer=InMemorySaver(),   # REQUIRED — the pause has to be stored
)
```

- `True` allows all four decision types; an `InterruptOnConfig` narrows them
  (`{"allowed_decisions": ["approve", "reject"]}`)
- The run **stops** and returns `result["__interrupt__"]` describing what it wants to do
- Each fresh interrupt needs a **fresh `thread_id`** — reusing one resumes the resolved run

---

# The Four Decisions

```python
agent.invoke(Command(resume={"decisions": [decision]}), config=config)
```

| Decision | Effect |
| --- | --- |
| `{"type": "approve"}` | tool runs with the **original** arguments |
| `{"type": "reject", "message": ...}` | tool skipped; your message goes back to the model |
| `{"type": "edit", "edited_action": {...}}` | tool runs with **your** arguments |
| `{"type": "respond", "message": ...}` | tool skipped; your text becomes its result |

**Next (ep. 14):** the same pause, applied declaratively to filesystem paths.
