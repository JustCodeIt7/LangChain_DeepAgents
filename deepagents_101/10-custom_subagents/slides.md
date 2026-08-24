---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 10 — Customizing Subagents

*Its own tools, its own model — or any compiled LangGraph runnable*

---

# Declarative: Own Tools, Own Model

```python
converter = {
    "name": "converter",
    "description": "Converts Celsius temperatures to Fahrenheit...",
    "system_prompt": "Always use the celsius_to_fahrenheit tool.",
    "tools": [celsius_to_fahrenheit],   # REPLACES the inherited set
    "model": MODEL,                     # overrides the orchestrator's model
}
```

- `tools` **replaces**, it does not add — the subagent sees only what you list
- `model` is where you drop in a **cheaper or larger** model for that sub-task

---

# Compiled: Bring Your Own Graph

```python
haiku_graph = create_agent(model=MODEL, system_prompt="Write one three-line haiku.")
poet = {"name": "poet", "description": "Writes a haiku...", "runnable": haiku_graph}
```

- `runnable=` makes it a **`CompiledSubAgent`** — reuse an agent you already built, unchanged
- Anything that compiles to a LangGraph runnable qualifies
- One orchestrator can mix both flavours and route each sub-task to the right one

**Next (ep. 11):** stop parsing prose — get a typed object back with `response_format`.
