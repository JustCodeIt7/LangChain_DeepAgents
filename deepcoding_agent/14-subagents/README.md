# Part 13 — Sessions That Survive a Restart

**Adds:** SQLite persistence. Quit, come back tomorrow, `/resume`, and the agent remembers.
**Diff:** ~115 lines (new: `sessions.py`; changed: `agent.py`, `widgets.py`, `tui.py`, `commands.py`)

**New dependency:** `pip install langgraph-checkpoint-sqlite`

## What's new

- **`SqliteSaver`** replaces `InMemorySaver` — one line in `agent.py`, and every checkpoint now
  lands in `<workdir>/.deepcoder/sessions.db`. `check_same_thread=False` because the agent runs in
  a worker thread while Textual owns the main one.
- **`threads.json`, our own index** — a checkpointer can *replay* a thread but can't *list* them
  nicely. A resume picker needs titles, so `sessions.remember()` records `thread_id → first
  message + timestamp` on every submit.
- **`sessions.history()`** — `agent.get_state(config)` returns the latest checkpoint; its
  `messages` list is the whole conversation, which is all the chat log needs to redraw itself.
- **`ResumeScreen`** — an `OptionList` modal. Picking a row swaps `thread_id` and replays the
  history into the chat. `push_screen(screen, callback)` is the non-blocking sibling of
  Part 10's `push_screen_wait`.
- **Storage is per-project on purpose** — sessions live in the workdir like `.git` does, not in
  `~/.deepcoder`. Point DeepCoder at another project and you get that project's history.

## Talking points

1. The demo that sells it: tell it a codename, **kill the app**, restart, `/resume`, ask for the
   codename back. (This part's build was verified across two separate Python processes.)
2. Draw the two layers: LangGraph checkpoints (turn state) vs. our index (titles). Why both exist.
3. `.deepcoder/` is gitignored — conversation history doesn't belong in your repo.
4. Note `/new` now means "new persistent thread", not "wipe memory".

## Run it

```bash
cd deepcoding_agent/13-sessions
python main.py
```

Chat a little, `ctrl+c`, run it again, `/resume`, pick the conversation.

## Files in this snapshot

| File | Role |
|---|---|
| `sessions.py` | Checkpointer factory, thread index, history replay |
| `widgets.py` | Adds `ResumeScreen` |
| `tui.py` | `pick_thread()` + remembers threads on submit |
| `commands.py` | Adds `/resume` |
| `agent.py` | Swaps in the SQLite checkpointer |

## Extend this yourself

1. Ask the agent to *summarize* the conversation and store that as the thread title instead of the
   first message.
2. Add `/delete-thread` that removes a thread from both the index and the checkpointer.
3. Show relative timestamps ("2h ago") in the picker.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
