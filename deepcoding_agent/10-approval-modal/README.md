# Part 10 — The Approval Modal

**Adds:** Safety comes back to the GUI. A pause opens a modal listing every pending action.
**Diff:** ~130 lines (new: `widgets.py`; changed: `tui.py`, `agent.py`, `app.tcss`)

## What's new

- **`widgets.py` / `ApprovalScreen(ModalScreen[list[dict]])`** — the type parameter says what the
  screen *returns*: the decisions list. Keys (`y`/`n`/`a`/`esc`) and buttons share the same actions.
- **`call_from_thread(self.push_screen_wait, ...)`** — the worker thread blocks here until the human
  answers. This is the sanctioned way for a worker to ask the UI a question and wait for the reply.
- **`interrupt_on` restored** in `agent.py`, now that there's somewhere to ask.
- **The session allowlist** — "always" adds the tool names to `app.allowlist`; a later batch whose
  tools are all allowlisted skips the modal entirely.
- **The resume loop moves into the worker** — `run_turn` is now a `while` loop that streams, pauses,
  asks, resumes, and keeps going until the turn actually ends.

## The modal renders a LIST, and that's the point

One pause carries **every** gated call from that model turn. Ask for *"write a file and run echo
hi"* and you get one interrupt with two `action_requests` — the modal shows both, and `dismiss()`
returns **two** decisions in the same order. A single-action modal would raise `ValueError` deep in
the graph the first time the model batches calls.

`test_modal_lists_every_pending_action` exists specifically to catch that regression.

## Talking points

1. Trace the thread hop: worker → `call_from_thread` → modal on the UI thread → result → worker.
2. Show the batched case live: one prompt, two actions, one dialog.
3. Press `a`, then ask for another file — no dialog. Explain session-scoped trust.
4. Note what you still can't see: *what* the file will contain. That's Part 16's diff view.

## Run it

```bash
cd deepcoding_agent/10-approval-modal
python main.py
```

Try: `Create m.txt with hello and also run echo hi — both in one turn.`

## Files in this snapshot

| File | Role |
|---|---|
| `widgets.py` | `ApprovalScreen` and its `summarize()` |
| `tui.py` | Worker resume loop + `ask_permission()` |
| `agent.py` | Restores `interrupt_on` |
| `app.tcss` | Modal styling |

## Extend this yourself

1. Add per-action checkboxes so you can approve one call and reject the other in the same batch.
2. Add a "reject with a reason" input so the model learns *why* you said no.
3. Colour-code the actions: red for `execute` and `delete`, yellow for writes.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
