# Part 05 — Asking Permission

**Adds:** Human-in-the-loop approvals. Risky tools pause and ask before they run.
**Diff:** ~85 lines (changed: `main.py`, `agent.py`, `config.py`)

## What's new

- **`interrupt_on={tool: True}`** — pauses the graph *before* a gated tool executes. We gate
  `execute`, `write_file`, `edit_file`, `delete`; read-only tools (`ls`, `read_file`, `glob`,
  `grep`) still run freely.
- **The checkpointer becomes load-bearing.** Pausing means storing a half-finished run and
  resuming it later. Without a checkpointer, `interrupt_on` can't work at all.
- **`result["__interrupt__"]`** — how a pause surfaces. `interrupts[0].value["action_requests"]`
  is the list of what the agent wants to do.
- **`Command(resume={"decisions": [...]})`** — how you answer. Decision types are `approve`,
  `reject`, `edit`, `respond`.
- **An "always" allowlist** — a local convenience meaning "approve, and stop asking about this
  tool for the rest of the session."

## ⚠️ The trap: one pause, many actions

**`decisions` is a list because one interrupt can carry several pending tool calls.** When the
model decides to write a file *and* run the tests in the same turn, you get **one** interrupt with
**two** `action_requests` — and your `decisions` list must have exactly two entries, in the same
order. A length mismatch raises `ValueError` from deep inside the graph, with a traceback that
won't point you here.

Writing a single-action approval handler is the single easiest way to break this app. It will work
in every demo until the first time the model batches two calls. Part 10's approval modal has to
render this as a *list* for the same reason.

Also note: a turn can pause **more than once** (approve the write, then the model wants to run the
tests), so `ask()` is a `while` loop, not one check.

## Talking points

1. Run Part 4 and Part 5 side by side with the same destructive request.
2. Show the approve → reject → always progression; reject with a reason and watch the model adapt.
3. Force the batched case: *"In one turn, write a file AND run a command."* Then explain the list.
4. Note what's still missing: you approve `edit_file` without seeing the diff. That's Part 16.

## Run it

```bash
cd deepcoding_agent/05-approvals
python main.py
```

Try: `Create a file note.txt containing hello.` → `y`
Then: `In one turn, write run.py and also execute echo hi.` → two prompts, one pause.

`DEEPCODER_AUTO_APPROVE=1` skips every prompt — for demos only.

## Files in this snapshot

| File | Role |
|---|---|
| `config.py` | Adds `GATED_TOOLS`, `AUTO_APPROVE` |
| `agent.py` | Adds `interrupt_on` |
| `main.py` | `decide()`, `summarize()`, and the resume loop in `ask()` |

## Extend this yourself

1. Add an `[e]dit` option using `{"type": "edit", "edited_action": {...}}` to fix a command before it runs.
2. Gate `execute` only when the command matches a risky pattern (`rm`, `git push`, `curl`).
3. Log every decision to a file so you have an audit trail of what the agent did.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
```
