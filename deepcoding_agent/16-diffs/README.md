# Part 16 — Seeing the Diff Before You Approve

**Adds:** File-changing actions show a syntax-highlighted unified diff in the approval modal.
**Diff:** ~55 lines (changed: `widgets.py`, `app.tcss`)

## What's new

- **`diff_for(action)`** — computes the _after_ text exactly the way the tool will, then hands both
  versions to `difflib.unified_diff`:
  - `write_file` → `content` replaces the whole file
  - `edit_file` → `old_string` → `new_string`, once (or everywhere with `replace_all`)
  - anything else → `None`, so `execute` and friends don't grow a pointless diff
- **`Syntax(diff, "diff")` inside a `Static`** — Textual hosts Rich renderables directly, so
  `+`/`-` colouring costs nothing extra and adds no dependency.
- **Virtual → real path mapping** — the model says `/calc.py`; the file lives at
  `WORKDIR/calc.py`. `_current_text()` does that translation (`lstrip("/")`) and returns `""` for
  a file that doesn't exist yet, which renders as an all-additions diff for new files.

## Why this part matters most

Part 5 gave you a veto. But approving `edit_file: /calc.py` tells you _nothing_ about what changes
— you were clicking yes on faith. Now you approve the actual change. This is the difference between
a safety prompt and a safety _feature_, and it's the closest DeepCoder gets to how Claude Code and
opencode feel.

## Talking points

1. Plant `return a - b` in a file, ask for a fix, and read the `-`/`+` lines in the dialog before
   pressing `y`. (That exact flow was used to verify this part.)
2. Show a _new_ file: the diff is all `+` lines, because "before" is empty.
3. Explain why the app recomputes the after-text rather than asking the tool: the tool hasn't run
   yet — that's the whole point.
4. Note the tradeoff: this reimplements the tool's edit semantics, so it must stay in sync with them.

## Run it

```bash
cd deepcoding_agent/16-diffs
python main.py
```

Try: put a bug in `workspace/calc.py`, then `calc.py subtracts but should add — fix it.`

## Files in this snapshot

| File         | Role                                                         |
| ------------ | ------------------------------------------------------------ |
| `widgets.py` | `_current_text()`, `diff_for()`, diff rendering in the modal |
| `app.tcss`   | `.diff` styling (scrolls past 12 lines)                      |

## Extend this yourself

1. Add a keybinding to expand a long diff full-screen.
2. Show a `+3 −1` summary line next to each action.
3. Warn in red when a `write_file` would overwrite an existing non-empty file.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
