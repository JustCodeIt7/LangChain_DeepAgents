# Part 17 — Startup Checks and Keybindings

**Adds:** DeepCoder tells you what's wrong before it fails, and grows real keyboard shortcuts.
**Diff:** ~65 lines (new: `health.py`; changed: `tui.py`)

## What's new

- **`health.py`** — checks the two things that actually break on a fresh machine:
  Ollama not running, and the model not pulled. Both otherwise surface as a confusing error deep
  inside an HTTP client, _after_ the user types their first question.
- **`urllib`, not a new dependency** — `GET /api/tags` with a 2-second timeout is the whole check.
- **Actionable messages** — not "connection refused" but "run `ollama serve`", and for a missing
  model, a list of the ones you _do_ have.
- **Non-Ollama providers are skipped** — a cloud model's missing API key reports itself clearly
  already; a false warning would be worse than none.
- **`BINDINGS`** — `esc` cancel, `ctrl+l` clear, `ctrl+n` new, `ctrl+r` resume, `f1` help. Each
  action delegates to the existing command, so there is exactly one implementation of each.
  Textual's `Footer` lists them automatically.

## Talking points

1. Stop Ollama (`pkill ollama`), start DeepCoder, and read the warning. Then set
   `DEEPCODER_MODEL=ollama:nope` and read the other one.
2. The principle: check the cheap preconditions at startup; the alternative is the user blaming
   your app for a `ConnectionRefusedError` they can't interpret.
3. Bindings delegate to commands — one behaviour, two front doors, no drift.
4. `Footer` is free documentation; keybindings you can't discover may as well not exist.

## Run it

```bash
cd deepcoding_agent/17-health-polish
python main.py
```

Press `f1`. Try `ctrl+n`, `ctrl+r`, `ctrl+l`.

## Files in this snapshot

| File        | Role                                                       |
| ----------- | ---------------------------------------------------------- |
| `health.py` | Ollama reachability + model-pulled checks                  |
| `tui.py`    | Runs the check on mount; adds `BINDINGS` and their actions |

## Extend this yourself

1. Warn when `DEEPCODER_WORKDIR` is a git repo with uncommitted changes — that's when an agent is
   riskiest.
2. Check `num_ctx` against the model's real context length and warn if it's larger.
3. Add a `/doctor` command that re-runs every check on demand.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
