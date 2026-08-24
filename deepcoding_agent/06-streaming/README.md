# Part 06 — Streaming

**Adds:** `runner.py` — the event layer. Answers stream token by token, and every UI from here on
consumes the same events.
**Diff:** ~141 lines (new: `runner.py`; changed: `main.py`, `agent.py`)

> **Approvals are OFF in this part.** One new idea at a time: this part is only about the stream.
> Part 7 turns the gates back on, as an event. Use a throwaway `DEEPCODER_WORKDIR` here.

## What's new

- **`runner.py`** — converts the raw LangGraph stream into three small dataclass events:
  `Token`, `ToolStart`, `Done`. Nothing in it knows what UI it feeds.
- **Two stream modes at once** — `stream_mode=["updates", "messages"]`. With a list, each chunk
  arrives as a `(mode_name, payload)` tuple:
  - `"updates"` → one chunk per graph step; where tool calls and `__interrupt__` appear.
  - `"messages"` → `(chunk, metadata)` tuples, token by token. **Unpacking this wrong is the most
    common streaming bug** — it's a tuple, not a plain chunk.
- **`usage_metadata`** — token counts ride along on the final assistant chunk.
- **A sync generator, deliberately.** It works in a `for` loop now and inside a Textual thread
  worker in Part 8 *without changing shape*. That decision is why `runner.py` never needs a rewrite.

## The bug this part taught me

The first version announced `write_file` **three times** for one action: once when the model
requested it, again at the approval prompt, again on resume. Resuming replays the message that
requested the tool, so the same call is seen more than once. The fix is to dedupe on each tool
call's stable `id`, with the `seen` set living in the *caller* so it survives across the pause.

## Talking points

1. Run Part 5 and Part 6 with the same prompt — the wait goes from "frozen" to "watchable".
2. Why an event layer instead of printing from inside the stream loop: this is the seam that makes
   the TUI possible without rewriting agent code.
3. Walk the `(mode, data)` unpacking and the nested `(chunk, meta)` tuple.
4. Show the duplicate-tool-line bug and the id-based fix — it's a great "streams replay" lesson.

## Run it

```bash
cd deepcoding_agent/06-streaming
python main.py
```

Try: `Write fizzbuzz.py, then run it.` — watch tool lines and tokens interleave.

## Files in this snapshot

| File | Role |
|---|---|
| `runner.py` | Event definitions and `run_turn()` — the layer every later UI uses |
| `main.py` | Renders events by printing them |
| `agent.py` | Drops `interrupt_on` for this part only |
| `config.py` | Unchanged |

## Extend this yourself

1. Add a `ToolEnd` event carrying the tool's result, and print it dimmed under the tool line.
2. Add elapsed-time tracking to `Done` and print "answered in 4.2s".
3. Swap `print` for `rich.live.Live` to re-render a Markdown answer as it streams.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
```
