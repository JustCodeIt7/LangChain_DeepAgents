# Part 08 — A Real Terminal UI

**Adds:** Textual. DeepCoder stops being a print loop and becomes an app — and then freezes.
**Diff:** ~140 lines (new: `tui.py`, `app.tcss`, `test_smoke.py`; changed: `main.py`, `agent.py`)

**New dependency:** `pip install textual`

## What's new

- **`tui.py`** — a `DeepCoderApp(App)` with `compose()` yielding `Header`, a scrollable `#chat`,
  an `Input`, a status line, and `Footer`.
- **`app.tcss`** — Textual CSS. Note `height: 1fr` on the chat log: it takes whatever space the
  other widgets don't.
- **`DeepCoderApp(agent=...)`** — the app accepts an injected agent. That one parameter is what
  makes the UI testable without a model.
- **`test_smoke.py`** — a headless test via `App.run_test()` and a `Pilot`. It types a question and
  asserts both messages render, in about two seconds, with no Ollama and no terminal. Uses the
  `anyio` pytest plugin, which is already installed — no new test dependency.
- **Approvals off again** — this UI has nowhere to ask the question yet. Part 10 adds the modal.

## The freeze is the lesson

`on_input_submitted` calls `runner.run_turn()` **directly on the UI thread**. Textual can't redraw,
can't scroll, can't even echo your keystrokes until the whole answer arrives. Ask it something slow
and the app looks crashed.

Don't skip past this. Part 9's worker fix is a two-line idea that only lands if you've felt the
freeze first. It's also why the answer appears all at once here despite `runner.py` streaming
perfectly — nothing can repaint mid-turn.

## Talking points

1. Build the layout live; show `1fr` doing the work by resizing the terminal.
2. Type a question and sit in the freeze. Try scrolling. Nothing moves.
3. Show `export_screenshot()` / `run_test()` — you can develop a TUI without a terminal at all.
4. Why the agent is a constructor argument: dependency injection makes the smoke test possible.

## Run it

```bash
cd deepcoding_agent/08-textual-shell
python main.py
```

Quit with `ctrl+c`. Command palette is `ctrl+p`.

## Files in this snapshot

| File | Role |
|---|---|
| `tui.py` | The Textual app: layout + (blocking) submit handler |
| `app.tcss` | Styling |
| `test_smoke.py` | Headless UI test |
| `main.py` | Now just builds the app and calls `.run()` |

## Extend this yourself

1. Add a `Static` above the input showing a spinner while the turn runs — then watch it *not*
   animate, because the UI thread is blocked. Perfect setup for Part 9.
2. Change the theme with `App.theme = "nord"` and restyle the chat bubbles.
3. Add a `BINDINGS` entry so `ctrl+l` clears the chat log.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
