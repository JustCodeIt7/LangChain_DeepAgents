---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 18 — Context Management

*Long conversations get compressed automatically — here we force it early to watch*

---

# Trigger and Keep

```python
summarizer = SummarizationMiddleware(
    model=MODEL,
    trigger=("messages", 4),   # summarize once history exceeds 4 messages
    keep=("messages", 2),      # keep the 2 newest verbatim
)
agent = create_deep_agent(model=MODEL, middleware=[summarizer], checkpointer=InMemorySaver())
```

- Every deep agent **already** summarizes — but only near ~85% of the context limit
- Because `.name` matches the built-in, deepagents **replaces** the default instead of stacking a second one
- Without it the count climbs 2, 4, 6, 8, 10… with it, the history **plateaus**

---

# Compression Is Not Amnesia

```python
agent.invoke({"messages": [{"role": "user", "content":
    "Remind me: when am I going, and with whom?"}]}, config=CONFIG)
```

- Details from the summarized turns are **still answerable** — fewer tokens, same knowledge
- The other half of context management is automatic too: tool results over **~20k tokens**
  are written to a file in the backend and replaced with a **preview + path**
- The agent `read_file`s it back on demand — one giant API response can never blow up the conversation

**Next (ep. 19):** everything at once — the capstone research agent.
