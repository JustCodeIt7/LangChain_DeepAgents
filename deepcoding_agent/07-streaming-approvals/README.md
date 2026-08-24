# Part 07 — Approvals, Streamed

**Adds:** Approvals come back, this time as an event. A pause no longer ends the turn — the
renderer answers it and the same turn resumes mid-stream.
**Diff:** ~75 lines (changed: `runner.py`, `agent.py`, `main.py`)

## What's new

- **`ApprovalNeeded`** — a fifth event type carrying the full `actions` list from the interrupt.
- **`resume_with(decisions)`** — builds the `Command(resume={"decisions": [...]})` payload.
  Keeping it in `runner.py` means no UI ever has to know that shape.
- **`interrupt_on` is back** in `agent.py`, now that the event layer can express a pause.
- **The resume loop** — `run_turn` *returns* on a pause; the caller collects decisions and calls
  `run_turn` again with the resume command. Same `thread_id`, same `seen` set, one continuous turn.

## Why this is a separate part from streaming

Part 6 deliberately turned approvals **off**. Two hard ideas — "the stream is a sequence of typed
events" and "a paused graph resumes from a checkpoint" — are much easier one at a time. Splitting
them also kept both parts inside the 150-line budget, which is the honest reason.

## Still the batched-list trap

`decisions` must match `actions` one-to-one, in order. See Part 5 — nothing about that changes
because the pause now arrives as an event. Part 10's modal renders the same list in a UI.

## Talking points

1. Trace one turn: `ToolStart` → `ApprovalNeeded` → (human) → resume → `Token`s → `Done`.
2. Why `run_turn` returns rather than blocking for input: the runner must never own the UI. That's
   exactly what lets Part 8 answer the same event from a modal instead of `input()`.
3. Reject something and watch the model recover inside the same conversation.

## Run it

```bash
cd deepcoding_agent/07-streaming-approvals
python main.py
```

Try: `Write ok.txt containing yes, then confirm.` → `y`

## Files in this snapshot

| File | Role |
|---|---|
| `runner.py` | Adds `ApprovalNeeded` + `resume_with()` |
| `main.py` | `decide()` and the resume loop, driven by events |
| `agent.py` | Restores `interrupt_on` |

## Extend this yourself

1. Add a 10-second timeout to `decide()` that auto-rejects, so an unattended run can't hang.
2. Emit a `Resumed` event so the UI can show "continuing…" after an approval.
3. Support `{"type": "edit"}` to fix a command's arguments before it runs.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
```
