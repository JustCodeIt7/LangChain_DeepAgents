---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 17 — Streaming

*Two modes, two very different UIs*

---

# `"updates"` — One Chunk Per Step

```python
for chunk in agent.stream(payload, stream_mode="updates"):
    for node_name, update in chunk.items():
        ...
```

- Each chunk is `{node_name: state_update}` — what **just happened**
- This is what you render as *"Thinking…"*, *"Calling add…"*, *"Done"*
- Pull `tool_calls` off the messages in the update to name the step

---

# `"messages"` — Tokens as They Arrive

```python
for message_chunk, metadata in agent.stream(payload, stream_mode="messages"):
    if metadata.get("lc_source") == "summarization": continue
    if message_chunk.__class__.__name__ != "AIMessageChunk": continue
```

- ⚠️ This mode yields **`(chunk, metadata)` tuples** — unpacking it wrong is *the* common bug
- It emits **every** message, tool results included: filter to `AIMessageChunk` and
  drop internal machinery like summarization
- `subgraphs=True` also surfaces subagent internals as `(namespace, chunk)`

**Next (ep. 18):** what happens when the conversation outgrows the context window.
