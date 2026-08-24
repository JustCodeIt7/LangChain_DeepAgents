# Part 04 — Running Shell Commands

**Adds:** The `execute` tool. The agent can now run the code it just wrote.
**Diff:** ~35 lines (changed: `agent.py`, `config.py`, `main.py`)

## What's new

- **`LocalShellBackend`** replaces `FilesystemBackend` as the default route. It's the same
  filesystem backend plus an `execute` tool — that one addition is what separates a file editor
  from a coding agent.
- **`inherit_env=True`** — not optional in practice. The default env is **empty**, so there's no
  `PATH` and every command is "command not found". The failure looks like a broken agent rather
  than a config choice. The tradeoff is real: your environment, secrets included, is visible to
  whatever the model runs.
- **`timeout=SHELL_TIMEOUT`** (120s default) — long enough for a test suite, short enough that a
  hung command doesn't freeze the session.
- **Two views of one directory** (a genuine gotcha, found while building this part): file tools use
  *virtual* paths rooted at `/`, but `execute` runs in a shell whose cwd is *already* the project
  root and reports **real** absolute paths from `pwd`. A model that copies a path out of `pwd`
  output will create a nested duplicate directory. The system prompt now spells the rule out.

## Talking points

1. The moment it becomes a coding agent: write a test, run it, read the failure, fix it.
2. Read the `LocalShellBackend` warning out loud — `subprocess.run(shell=True)`, no sandbox,
   irreversible. This part is deliberately the *unsafe* checkpoint.
3. Ask it to run something mildly destructive and note that nothing stops it. That's Part 5.
4. Show the `pwd`-vs-virtual-path trap and why the prompt has to disambiguate.

## Run it

```bash
cd deepcoding_agent/04-shell-execute
python main.py
```

Try: `Write add.py with an add(a,b) function, then run it to prove 2+3=5.`

## Safety

The agent runs commands **on your machine, as you, with no confirmation**. Keep `DEEPCODER_WORKDIR`
pointed at a throwaway directory until Part 5 adds approvals. Never point this part at a repo you
care about.

## Files in this snapshot

| File | Role |
|---|---|
| `config.py` | Settings + the shell-aware system prompt |
| `agent.py` | Swaps in `LocalShellBackend` |
| `main.py` | Unchanged REPL |

## Extend this yourself

1. Set `DEEPCODER_SHELL_TIMEOUT=5` and ask it to run `sleep 30` — watch the timeout fire.
2. Drop `inherit_env=True` and run `python --version` to see the empty-PATH failure firsthand.
3. Ask it to write a failing pytest, run it, and fix the code until it passes.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
```
