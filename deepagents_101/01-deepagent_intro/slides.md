---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 01 — Your First Deep Agent

*One function call gives you an agent with a filesystem, planning, and subagents*

---

# What You Get for Free

```python
agent = create_deep_agent(model=MODEL, system_prompt=instructions)
```

- **No `tools=` argument** — the built-in suite comes with the agent:
  - **Filesystem**: `ls` · `read_file` · `write_file` · `edit_file` · `delete` · `glob` · `grep`
  - **`execute`** — shell (ep. 07)
  - **`task`** — delegate to subagents (ep. 09)
  - **`write_todos`** — planning (ep. 04)

---

# Run It and Inspect

```python
result = agent.invoke({"messages": [{"role": "user", "content": question}]})
```

- `result["messages"]` — the full conversation, tool calls included; `[-1]` is the final answer
- `result["files"]` — the agent's **virtual filesystem** (empty here — ep. 05)
- `text_of()` — normalizes message content across providers (Ollama: string, OpenAI: content blocks)

**Next (ep. 02):** the two ways to specify a model — and where your system prompt lands.
