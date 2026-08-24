# Part 03 — Real Project Files

**Adds:** The agent stops talking about code and starts editing it — real files, on real disk.
**Diff:** ~95 lines (new: `config.py`, `agent.py`; changed: `main.py`)

## What's new

- **`config.py`** — every setting in one place, so no other module calls `os.getenv()`.
- **`agent.py`** — `build_model()` / `build_backend()` / `build_agent()`. Construction moved out
  now because it finally has enough moving parts to crowd the REPL.
- **`CompositeBackend`** — routes paths to different storage:
  `/scratch/` → `StateBackend` (in-memory), everything else → `FilesystemBackend(root_dir=WORKDIR)`.
  The scratch route isn't decorative: deepagents writes its own bookkeeping (large tool results,
  conversation history) through this backend, and without the route that machinery litters your
  project directory.
- **Model instance instead of a string** — passing `init_chat_model(...)` output rather than
  `"ollama:..."` is what lets us set Ollama-specific options:
  - **`num_ctx=8192`** — Ollama's default context is small, and it truncates **silently**. This is
    the real cause of "why did my agent forget the file it just read?"
  - **`keep_alive="30m"`** — stops Ollama unloading a 6 GB model between turns.

## Talking points

1. Show `ls`/`read_file`/`write_file` actually hitting disk — `cat workspace/hello.py` after a turn.
2. Why `WORKDIR` is a sandbox boundary, and why that's the honest answer to "is this safe?" (for now).
3. The `num_ctx` trap — demo an agent "forgetting" with a small context, then fix it.
4. Note the agent sometimes ends a turn on the tool call with no closing text. That's a small-model
   quirk, and it's the motivation for streaming in Part 6.

## Run it

```bash
cd deepcoding_agent/03-project-files
python main.py
```

Try: `Create a file called hello.py with a hello_world() function.` then `cat workspace/hello.py`.

The workdir defaults to `./workspace` and is created on start. Override with `DEEPCODER_WORKDIR`.

## Files in this snapshot

| File | Role |
|---|---|
| `config.py` | All settings, read from env once |
| `agent.py` | Model, backend routing, and agent assembly |
| `main.py` | The REPL and one-turn `ask()` helper |

## Extend this yourself

1. Point `DEEPCODER_WORKDIR` at a real project of yours and ask the agent to explain its layout.
2. Add a `/files` command that lists the workdir without involving the model.
3. Add a second route (e.g. `/notes/` → `StateBackend`) and see which files survive a restart.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
```
