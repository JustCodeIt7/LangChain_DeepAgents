# Part 12 — Slash Commands

**Adds:** `/help`, `/new`, `/clear`, `/model`, `/quit` — with autocomplete. Things the user does,
which the model never sees.
**Diff:** ~105 lines (new: `commands.py`; changed: `tui.py`)

## What's new

- **`commands.py`** — a registry built by introspection: every `cmd_*` method is a command, its
  docstring is its `/help` line. Adding a command is writing one method.
- **Dispatch before the agent** — `submit()` checks for a leading `/` and short-circuits. Commands
  are free and instant; no tokens, no thread, no model.
- **`SuggestFromList`** — pass a `suggester` to `Input` and Textual ghost-completes `/comm…` as you
  type (accept with →).
- **`/model`** — swaps the model *mid-session* by rebuilding the agent. The checkpointer keeps the
  thread, so the new model inherits the old conversation. `/new` also clears the allowlist —
  trust shouldn't outlive the conversation that granted it.

## Talking points

1. The dividing line: slash = instruction to the *app*, plain text = message to the *model*.
2. Build a command live on camera — `cmd_workdir` is a good one (show the current workdir).
3. Switch `/model ollama:qwen3.5:4b` mid-chat and ask the same question again; compare.
4. Why introspection beats an if/elif chain: `/help` can never drift out of date.

## Run it

```bash
cd deepcoding_agent/12-slash-commands
python main.py
```

Type `/` and watch the ghost completion. Try `/model` with no argument, then with one.

## Files in this snapshot

| File | Role |
|---|---|
| `commands.py` | The registry: five commands + dispatch + completion names |
| `tui.py` | Short-circuits `/` input; wires the suggester |

## Extend this yourself

1. Add `/workdir <path>` that re-points `config.WORKDIR` and rebuilds the agent.
2. Add `/tokens` showing per-turn history, not just the running total.
3. Add `/theme <name>` cycling `self.app.theme` — instant dark/light switching.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
