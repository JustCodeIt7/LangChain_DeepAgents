# Part 02 — A Chat Loop With Memory

**Adds:** A REPL, and the checkpointer that makes the agent remember what you said two turns ago.
**Diff:** ~60 lines (changed: `main.py`)

## What's new

- **`checkpointer=InMemorySaver()`** — saves graph state after every step. Without it, every
  `.invoke()` starts from an empty message list and the agent has amnesia.
- **`thread_id`** — passed as `config={"configurable": {"thread_id": ...}}`. It's the memory key:
  same id means the agent sees the whole prior conversation, a new id means a blank slate.
  `/new` just generates a new one.
- **A real REPL** — `input()` loop with `/new`, `/exit`, and graceful `Ctrl-C` / `Ctrl-D` handling.
  Ctrl-C during a slow model call cancels that turn rather than killing the app.
- **Error containment** — a failed turn prints in red and returns you to the prompt.

## Talking points

1. Demo the amnesia first: run Part 1 twice with a follow-up question, then show Part 2 remembering.
2. Checkpointer vs. thread: one stores state, the other selects _which_ state. Both are needed.
3. `InMemorySaver` dies with the process — flag that Part 13 swaps in SQLite for real sessions.
4. Why `/`-prefixed commands now: it establishes the convention the TUI expands on in Part 12.

## Run it

```bash
cd deepcoding_agent/02-chat-loop
python main.py
```

Try: `My favorite language is Rust.` then `What is my favorite language?` — then `/new` and ask again.

## Files in this snapshot

| File      | Role                                                              |
| --------- | ----------------------------------------------------------------- |
| `main.py` | Config, agent construction, the `ask()` turn helper, and the REPL |

## Extend this yourself

1. Add a `/model` command that rebuilds the agent with a different model string mid-session.
2. Print the message count each turn so you can watch context grow.
3. Keep a list of past thread_ids and add `/switch <id>` to jump between conversations.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
```
