---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 03 — Adding Your Own Tools

*A tool is just a Python function with a docstring — and yours are added, not swapped in*

---

# Two Ways to Write a Tool

```python
def word_count(text: str) -> int:
    """Count how many words are in the given text."""   # <- the model reads this
    return len(text.split())

@tool
def reverse_text(text: str) -> str:
    """Reverse the characters of the given text."""
    return text[::-1]
```

- **Plain function** — deepagents infers the schema from the signature + docstring
- **`@tool`** — same result, plus explicit control (name, args schema, `return_direct`)
- Keep parameter types simple (`str` / `int` / `bool`) — small models coerce them better

---

# `tools=` Is Additive

```python
agent = create_deep_agent(model=MODEL, tools=[word_count, reverse_text])
```

- Your tools sit **alongside** `ls` · `read_file` · `write_file` · `task` — nothing is removed
- Steer usage from the system prompt ("Do not use any filesystem tools")
- Inspect what actually ran: `message.tool_calls` on AI messages, `ToolMessage` for results

**Next (ep. 04):** multi-step work needs a plan — `TodoListMiddleware` and `write_todos`.
