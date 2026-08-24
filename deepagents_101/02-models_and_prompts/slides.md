---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 02 — Models and System Prompts

*Two ways to give the agent a brain — and where your system prompt actually lands*

---

# Two Ways to Specify a Model

```python
# A. string — any LangChain provider, default parameters
agent = create_deep_agent(model="ollama:qwen3.5:2b")

# B. instance — full control (temperature, max_tokens, base_url, ...)
llm = init_chat_model(MODEL, temperature=0)
agent = create_deep_agent(model=llm)
```

- **String** = simplest; **instance** = full control
- deepagents uses the instance **as-is**

---

# Where Your Prompt Lands

- `system_prompt` is placed **FIRST** — the framework's tool guidance is **appended after it**
- Your prompt steers **personality and behavior**; tool knowledge comes from the framework
- `debug=True` prints **every graph step** — verbose by design, keep the question tiny

**Next (ep. 03):** the agent only has built-in tools — add your own. A tool is just a Python function with a docstring.
