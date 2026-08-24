# Part 11 — The Plan Sidebar and Status Bar

**Adds:** You can watch the agent think: its todo list lives in a sidebar, and a status bar tracks
model, elapsed time, and token spend.
**Diff:** ~110 lines (changed: `runner.py`, `agent.py`, `tui.py`, `widgets.py`, `app.tcss`)

## What's new

- **`TodoListMiddleware`** — in deepagents 0.7 the `write_todos` tool is *opt-in*. Without this
  middleware the tool doesn't exist and the agent can't plan. One line in `middleware=[...]`.
- **`Plan` event** — the runner watches `updates` chunks for a `todos` key in the state and emits
  the whole list. `PlanPanel.show()` redraws it: `[x]` done, `[>]` in progress, `[ ]` pending.
- **Side-by-side layout** — `Horizontal(#body)` holds the chat and the plan; the panel stays
  hidden (`display = False`) until the first todo arrives.
- **The status bar is a timer, not an event** — `set_interval(1/2, refresh_status)` repaints
  model, workdir, elapsed, and cumulative tokens. Elapsed time ticks *while* the agent works
  because the UI thread is free — which quietly proves Part 9 worked.
- **Usage rides the `Finished` message** — the worker never touches `self.tokens`. Workers post
  messages; handlers mutate state. Same rule as always, now with a second reason to care.

## Talking points

1. Ask for a 3-step task and watch the plan appear before any file is touched.
2. Point at the elapsed counter ticking during a turn — that's the worker thread paying rent.
3. Token counts come from `usage_metadata` on the final chunk; Ollama reports real numbers.
4. Why the panel hides when empty: chrome should earn its pixels.

## Run it

```bash
cd deepcoding_agent/11-plan-status
python main.py
```

Try: `Use write_todos to plan, then create a.txt, b.txt and c.txt each containing its own name.`
(Small local models sometimes stop before finishing every step — ask them to continue.)

## Files in this snapshot

| File | Role |
|---|---|
| `runner.py` | Adds the `Plan` event |
| `agent.py` | Adds `TodoListMiddleware` |
| `widgets.py` | Adds `PlanPanel` |
| `tui.py` | Layout, `PlanUpdate` handler, status timer, usage on `Finished` |

## Extend this yourself

1. Show a progress ratio ("2/5 done") in the panel title.
2. Track tokens per turn as well as per session, and show both.
3. Persist the token total across restarts in `.deepcoder/stats.json`.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
