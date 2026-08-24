# Part 14 — Subagents

**Adds:** Delegation. A `code-reviewer` and a `test-runner` the main agent can hand work to, with
their inner tool calls streamed — indented — into the chat.
**Diff:** ~85 lines (changed: `agent.py`, `runner.py`, `tui.py`, `test_smoke.py`, `app.tcss`)

## What's new

- **`subagents=[...]`** — plain dicts: `name`, `description`, `system_prompt`, and optionally
  their own `interrupt_on`. deepagents exposes them through the built-in `task` tool; the
  *description* is what the main model reads when deciding to delegate.
- **Why subagents at all: context quarantine.** The reviewer reads five files to write five lines
  of findings. Without a subagent, those five files land in the main context forever. With one,
  the main agent sees only the report.
- **`subgraphs=True`** — every stream chunk becomes a 3-tuple `(namespace, mode, payload)`.
  `()` means the main agent; `("tools:<id>",)` means inside a delegated task. The runner marks
  events `nested=True` and the UI indents them with a `·`.
- **Subagent tokens are filtered out** — a subagent's *prose* is its scratchwork; only its final
  report (relayed by the main agent) belongs in the chat. Its *tool calls* are shown so you can
  watch it work.
- **`test-runner` keeps its own `interrupt_on`** — gates follow the tool, even one subagent deep.

## Talking points

1. Plant a bug in a file, delegate a review, and watch `task → code-reviewer` followed by an
   indented `· read_file`.
2. The namespace tuple: `()` vs `("tools:…",)` — worth showing raw once.
3. Small-model reality: qwen3.5:9b sometimes needs to be told to use the task tool explicitly, and
   sometimes ends without relaying the report. That's a model limitation, not an API one.
4. Where this scales: reviewer + implementer + tester is the shape every "agent team" product uses.

## Run it

```bash
cd deepcoding_agent/14-subagents
python main.py
```

Try: `Use the task tool with subagent_type='code-reviewer' to review mathy.py, then relay its findings.`

## Files in this snapshot

| File | Role |
|---|---|
| `agent.py` | Defines the two subagents |
| `runner.py` | `subgraphs=True`, 3-tuple unpacking, `nested` flag |
| `tui.py` | Indented nested tool lines; `task →` labels |

## Extend this yourself

1. Give `code-reviewer` a cheaper model (`"model": "ollama:qwen3.5:4b"`) — per-subagent models are
   one dict key away.
2. Add a `docs-writer` subagent gated on `write_file`.
3. Show a spinner row while a `task` is running and collapse its nested lines when it finishes.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
