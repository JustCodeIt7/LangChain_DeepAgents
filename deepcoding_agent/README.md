# DeepCoder — Build a Terminal Coding Agent in 18 Parts

Build a Claude Code / opencode-style coding agent from scratch, in Python, running entirely on
your own machine.

**Stack:** [deepagents](https://docs.langchain.com/oss/python/deepagents/) (on LangChain +
LangGraph) for the agent, [Ollama](https://ollama.com) for the model, and
[Textual](https://textual.textualize.io) for the terminal UI.

**The rules of the series:**
- Every part adds **≤150 lines** of code. No part dumps a finished app on you.
- Every part folder is a **complete, runnable snapshot**. `cd` into part 7, run it, and you get
  exactly what part 7 built.
- Everything runs **locally**. Your code never leaves your machine.

## Setup

```bash
conda activate py313          # or any Python 3.11+ environment
pip install deepagents langchain langchain-ollama langgraph rich python-dotenv
pip install textual                        # from part 8
pip install langgraph-checkpoint-sqlite    # from part 13
pip install langchain-mcp-adapters mcp     # part 18, optional
```

```bash
ollama pull qwen3.5:9b
```

Then:

```bash
cd 01-intro && python main.py
```

## Choosing a model

One environment variable controls every part:

```bash
export DEEPCODER_MODEL="ollama:qwen3.5:9b"   # the default
export DEEPCODER_MODEL="openai:gpt-5.5"      # any LangChain provider works
```

Other settings: `DEEPCODER_WORKDIR` (default `./workspace`), `DEEPCODER_NUM_CTX` (8192),
`DEEPCODER_KEEP_ALIVE` (30m), `DEEPCODER_SHELL_TIMEOUT` (120), `DEEPCODER_AUTO_APPROVE`.

**A note on small models.** The whole series was built and tested against `qwen3.5:9b`. It works,
but a 9B model sometimes ends a turn without a closing message, or needs to be told explicitly to
use a tool. That's a model limitation, not an API one — and worth seeing, because it's what
building on local models actually feels like.

## The parts

| # | Part | What you learn | New deps |
|---|------|----------------|----------|
| 01 | [intro](01-intro/) | `create_deep_agent`, model strings, the built-in toolbox | — |
| 02 | [chat-loop](02-chat-loop/) | Checkpointers and `thread_id`: why agents forget | — |
| 03 | [project-files](03-project-files/) | `CompositeBackend`, real files, the `num_ctx` trap | — |
| 04 | [shell-execute](04-shell-execute/) | `LocalShellBackend`, the `execute` tool, `inherit_env` | — |
| 05 | [approvals](05-approvals/) | `interrupt_on`, and why `decisions` is a **list** | — |
| 06 | [streaming](06-streaming/) | `runner.py`: the event layer, dual `stream_mode` | — |
| 07 | [streaming-approvals](07-streaming-approvals/) | Pauses as events; resuming mid-stream | — |
| 08 | [textual-shell](08-textual-shell/) | A real TUI — that freezes, on purpose | `textual` |
| 09 | [textual-worker](09-textual-worker/) | Thread workers, `post_message`, dropped-token bug | — |
| 10 | [approval-modal](10-approval-modal/) | `ModalScreen`, `call_from_thread`, batched actions | — |
| 11 | [plan-status](11-plan-status/) | `TodoListMiddleware`, plan sidebar, token counts | — |
| 12 | [slash-commands](12-slash-commands/) | A command registry with autocomplete | — |
| 13 | [sessions](13-sessions/) | `SqliteSaver` — conversations that survive a restart | `langgraph-checkpoint-sqlite` |
| 14 | [subagents](14-subagents/) | Delegation, context quarantine, `subgraphs=True` | — |
| 15 | [project-memory](15-project-memory/) | `AGENTS.md` via `memory=`, and `/init` | — |
| 16 | [diffs](16-diffs/) | See the diff before you approve it | — |
| 17 | [health-polish](17-health-polish/) | Startup checks, keybindings | — |
| 18 | [mcp-packaging](18-mcp-packaging/) | MCP tools, async/sync bridging, `pip install -e .` | `langchain-mcp-adapters` |

## The app at part 18

```
main.py       entry point: load MCP tools, start Textual
tui.py        the App: layout, worker, messages, handlers
runner.py     the event layer over agent.stream() — UI-agnostic
agent.py      model + backends + subagents + gates + memory
config.py     every setting, read from the environment once
widgets.py    approval modal (with diffs), resume picker, plan panel
commands.py   /help /new /clear /model /init /resume /quit
sessions.py   SQLite checkpointer + thread index + history replay
health.py     startup checks with actionable messages
mcp_tools.py  optional MCP servers, bridged to sync
app.tcss      styling
```

## Three traps worth knowing before you start

1. **`decisions` is a list.** One approval pause carries *every* gated tool call from that model
   turn. Write a single-action handler and it works until the model asks to write a file *and*
   run the tests in one turn — then it raises `ValueError` deep inside the graph. (Parts 5, 10.)
2. **`Markdown.update()` is awaitable.** Call it once per streamed token and the calls race, and
   tokens get silently dropped. Buffer, and repaint on a timer. (Part 9.)
3. **MCP tools are async-only.** They load fine, then raise `NotImplementedError` the first time
   the model calls one, unless you bridge them. (Part 18.)

Each is documented in the part where it bites, because each one bit during the build.

## Verifying a part

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio      # parts 8+, headless, no model needed
```

The Textual parts ship a `test_smoke.py` that drives the real app through a `Pilot` with a stub
agent — no terminal, no Ollama, about two seconds. Tests don't count toward the 150-line budget;
`python _tools/diff_lines.py` enforces it across all 18 parts.

## Related

- [`deepagents_101/`](../deepagents_101/) — 20 single-file episodes on the deepagents API itself.
  Start there if you want the library rather than the app.
