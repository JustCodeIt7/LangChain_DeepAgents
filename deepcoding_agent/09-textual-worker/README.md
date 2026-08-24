# Part 09 — Unfreezing the UI

**Adds:** A worker thread. The UI stays alive, text streams in live, and Esc cancels a turn.
**Diff:** ~120 lines (changed: `tui.py`, `test_smoke.py`, `app.tcss`)

## What's new

- **`@work(thread=True, exclusive=True)`** — `run_turn` moves off the UI thread. `exclusive=True`
  means starting a new turn cancels the previous one automatically.
- **`post_message()`, never a direct widget call** — the worker posts `Chunk` / `ToolLine` /
  `Finished`, and handlers named `on_chunk`, `on_tool_line`, `on_finished` update the UI back on
  the main thread. **That is the whole rule for thread safety in Textual.**
- **Lazy answer widget** — created on the first token, so tool lines that arrive first appear
  *above* the reply instead of below it.
- **Esc to cancel** — `worker.cancel()`, plus an `is_cancelled` check between events.

## Two real bugs this part taught me

**1. Racing `update()` drops tokens.** `Markdown.update()` returns an *awaitable* that re-parses
the document. Calling it once per token makes those calls race, and text gets lost — a five-token
answer rendered as just `"one "`, even though the buffer held all five. The fix is to accumulate
text in `on_chunk` and repaint on a `set_interval(1/20, ...)` timer. That's also much cheaper than
parsing Markdown per token. `on_finished` calls `repaint()` once more so the last tokens aren't
stranded between ticks.

**2. Cancellation is cooperative.** `worker.is_cancelled` is checked *between* events, so Esc can't
interrupt a blocked HTTP call to Ollama — it takes effect at the next chunk. That's a real
limitation of threads, not a bug to hide. Say so in the video.

## Talking points

1. Run Part 8, feel the freeze; run Part 9, type while it answers. `test_ui_stays_responsive`
   asserts exactly that.
2. Draw the thread boundary: worker → `post_message` → handler → widget. Nothing crosses it.
3. Demo the dropped-token bug by calling `update()` per token, then fix it with the timer.
4. Hit Esc mid-answer and narrate why it stops at the next chunk, not instantly.

## Run it

```bash
cd deepcoding_agent/09-textual-worker
python main.py
```

## Files in this snapshot

| File | Role |
|---|---|
| `tui.py` | Worker, messages, handlers, repaint timer, cancel action |
| `test_smoke.py` | Streaming test + a responsiveness test |
| `app.tcss` | Adds `.tool` styling |

## Extend this yourself

1. Show a spinner in `#status` while a worker runs — it will actually animate now.
2. Add a `ToolEnd` message so tool lines can turn into ✓ or ✗ when they finish.
3. Make the repaint interval configurable and watch 1 fps vs 60 fps.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
