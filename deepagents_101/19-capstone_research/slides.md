---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 19 — Capstone: A Research Agent

*Planning + a virtual filesystem + a specialist subagent + live streaming, in one agent*

---

# Assemble the Pieces

```python
agent = create_deep_agent(
    model=MODEL,
    backend=StateBackend(),                 # ep. 05 — the corpus lives here
    middleware=[TodoListMiddleware()],       # ep. 04 — planning
    subagents=[analyst],                     # ep. 09 — delegation
    system_prompt="You are a research lead. Workflow: ...",
)
```

- The **corpus** is seeded as virtual files (`/corpus/solar.md`, `wind.md`, `storage.md`) — no internet
- The **analyst** subagent reads *one* file and returns 2–3 bullets, so the long file contents
  never clog the orchestrator's history

---

# Run It, Watch It, Collect the Deliverable

```python
for chunk in agent.stream({"messages": [...], "files": seed_files}, stream_mode="values"):
    final_state = chunk        # "values" gives the FULL state each step
```

- The prompt spells out the workflow: **plan → `ls` → delegate each source → `write_file` the report**
- `stream_mode="values"` (not `"updates"`) because we want the files at the end, not just the deltas
- The payoff is a real artifact: `final_state["files"]["/report.md"]`

**Next (ep. 20):** tools from outside your codebase, over MCP.
