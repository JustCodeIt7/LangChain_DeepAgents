# Part 15 — Project Memory (AGENTS.md)

**Adds:** Standing instructions. The agent reads `AGENTS.md` before every run, and `/init` writes
one for you by exploring the project.
**Diff:** ~50 lines (changed: `agent.py`, `tui.py`, `commands.py`)

## What's new

- **`memory=["/AGENTS.md"]`** — one parameter. Files listed here are loaded into the system prompt
  at the **start of every run** (fresh read each turn, so edits apply immediately). A missing file
  is skipped silently — a brand-new project doesn't crash.
- **The path is backend-relative** — `/AGENTS.md` resolves through the same `CompositeBackend` as
  the file tools, so it means `<workdir>/AGENTS.md`. One mental model for all paths.
- **`/init`** — a command that *sends a prompt* instead of printing text. `submit()` grew a
  `send()` entry point so commands can start agent turns; `/init` asks the agent to explore with
  `ls`/`read_file` and write the guide. The write is gated like any other — you approve it.
- **Self-editing memory** — the agent can `edit_file` its own AGENTS.md. Tell it "always run tests
  after edits, remember that" and the rule persists for every future session.

## Talking points

1. Put a silly rule in AGENTS.md ("end every reply with BANANA") and show it obeyed with zero
   prompting. Then show the trap this build hit: a user prompt that *conflicts* with the rule
   ("reply in exactly two words") wins — standing instructions are context, not law.
2. Run `/init` on a real project and read what it wrote. (Live here, it even documented
   `.deepcoder/` as "do not modify manually".)
3. AGENTS.md is an emerging convention (agents.md) — same file works across coding agents.
4. Difference from Part 13: sessions remember *conversations*; memory remembers *rules*.

## Run it

```bash
cd deepcoding_agent/15-project-memory
python main.py
```

Try `/init`, approve the write, then `cat workspace/AGENTS.md`.

## Files in this snapshot

| File | Role |
|---|---|
| `agent.py` | Adds `memory=["/AGENTS.md"]` |
| `commands.py` | Adds `/init` |
| `tui.py` | Extracts `send()` so commands can start turns |

## Extend this yourself

1. Add `/remember <rule>` that appends a bullet to AGENTS.md without a model call.
2. Load a personal `~/.deepcoder/AGENTS.md` too — route a second memory path to a different backend.
3. Show a 📋 indicator in the status bar when AGENTS.md is present.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
