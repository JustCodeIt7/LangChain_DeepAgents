---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 09 — Delegating to Subagents

*The `task` tool spawns a helper with its own fresh context — you only get the answer back*

---

# Define One With a Dict

```python
critic = {
    "name": "critic",
    "description": "Critiques writing and returns exactly three bullet points...",
    "system_prompt": "You are a blunt writing critic. Reply with three bullets. Nothing else.",
}
agent = create_deep_agent(model=MODEL, subagents=[critic])
```

- **`description`** is read by the **orchestrator** to decide when to delegate — write it like a job posting
- **`system_prompt`** is read by the **subagent** once it is running
- Every deep agent also gets a built-in **`general-purpose`** subagent for free

---

# Context Isolation Is the Point

```python
call["name"] == "task"  ->  call["args"]["subagent_type"] == "critic"
```

- One `task` call goes out; **one consolidated result** comes back as a `ToolMessage`
- The subagent's internal turns **never enter** the orchestrator's message history
- That is how a long sub-job stays out of your main context window

**Next (ep. 10):** give a subagent its own tools and model — or plug in a compiled graph.
