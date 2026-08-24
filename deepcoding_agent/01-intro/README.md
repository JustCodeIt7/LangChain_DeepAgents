# Part 01 — Your First Coding Agent

**Adds:** A working agent in ~15 lines of real code, running entirely on your own machine.
**Diff:** ~80 lines (new: `main.py`)

## What's new

- **`create_deep_agent(model=..., system_prompt=...)`** — the single entry point. It returns a
  compiled LangGraph state machine with a filesystem toolbox already attached.
- **Model as a string** — `"ollama:qwen3.5:9b"` is `provider:model`. deepagents hands it to
  LangChain's `init_chat_model`, so switching to `"openai:gpt-5.5"` is a one-word change.
- **`text_of()`** — Ollama returns message content as a plain string; other providers return a list
  of content blocks. This helper normalizes both so nothing downstream has to care. For Ollama alone
  it's technically a no-op, but it's what keeps the series provider-swappable.
- **The result shape** — `.invoke()` returns the full state dict; `result["messages"][-1]` is the reply.

## Talking points

1. What "deep agent" means: a plan/filesystem/subagent-capable loop, not just a chat wrapper.
2. Why local models matter for a coding agent — your source never leaves the machine.
3. Tour the built-in tools (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `task`)
   and note they're on a _virtual_ filesystem right now. That's the hook for Part 3.
4. The agent has no memory yet — ask a follow-up question and watch it forget. Hook for Part 2.

## Run it

```bash
cd deepcoding_agent/01-intro
python main.py
```

```bash
python main.py "write a python function that reverses a string"
```

Requires Ollama running with the model pulled: `ollama pull qwen3.5:9b`.

## Files in this snapshot

| File      | Role                                                        |
| --------- | ----------------------------------------------------------- |
| `main.py` | Everything: config, agent construction, one-shot ask/answer |

## Extend this yourself

1. Change `DEEPCODER_MODEL` to `ollama:qwen3.5:4b` and compare speed vs. answer quality.
2. Rewrite `SYSTEM_PROMPT` to make DeepCoder answer only in Python, never prose.
3. Print `result["messages"]` in full to see the internal message list the agent builds.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
```
