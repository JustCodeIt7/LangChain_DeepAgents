---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 12 — Checkpointers and Threads

*Turn 2 remembers turn 1 — because the graph saves state after every step*

---

# Add a Checkpointer, Name the Thread

```python
agent = create_deep_agent(model=MODEL, checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "alice"}}
agent.invoke({"messages": [{"role": "user", "content": "..."}]}, config=config)
```

- The second `invoke` passes **no history** — the checkpointer reloads it from the thread
- `InMemorySaver` is for demos; swap in `SqliteSaver` / `PostgresSaver` to survive a restart
- Without a checkpointer every `invoke` starts from nothing

---

# One Deployment, Many Conversations

| thread_id | asks "what is my favourite number?" | answer |
| --- | --- | --- |
| `alice` | after saying it is 42 | **42** |
| `bob` | first message ever | *"I don't know"* |

```python
agent.get_state({"configurable": {"thread_id": "alice"}}).values["messages"]
```

- Different `thread_id` = a **completely separate** history — this isolation is how one agent serves many users
- `get_state()` reads back whatever the checkpointer holds

**Next (ep. 13):** pausing the agent before a risky tool runs, and letting a human decide.
