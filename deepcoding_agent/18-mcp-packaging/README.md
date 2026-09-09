# Part 18 — MCP Tools and Packaging

**Adds:** Borrowed tools via MCP, and a real `deepcoder` command. The series ends here.
**Diff:** ~130 lines (new: `mcp_tools.py`, `pyproject.toml`, `example_mcp_server.py`,
`mcp.json.example`; changed: `main.py`, `agent.py`, `tui.py`)

## What's new

- **`mcp_tools.py`** — reads `mcp.json`, starts each server, and hands its tools to the agent.
  Missing file, bad JSON, or a server that won't start: all return `[]` and DeepCoder runs anyway.
  An optional feature must never break startup.
- **`asyncio.run()` exactly once, before `App.run()`** — MCP clients are async; Textual owns the
  loop once it starts. Loading at startup keeps those two facts from colliding.
- **`tools=extra_tools`** — MCP tools sit alongside the built-ins, and are gated by the same
  approval rules if you add their names to `GATED_TOOLS`.
- **`pyproject.toml`** — `[project.scripts] deepcoder = "main:main"`. Because the modules are flat,
  `[tool.setuptools] py-modules` lists them explicitly. `pip install -e .` and the command exists.
  (Verified: the wheel builds with all ten modules and the entry point registered.)

## The bug this part taught me: async-only tools

MCP tools load fine and then **explode at call time**:

```
NotImplementedError: StructuredTool does not support sync invocation
```

`langchain-mcp-adapters` returns tools with a `coroutine` and no `func` — async-only — while
DeepCoder's runner is deliberately synchronous (Part 6, and everything since). The fix is
`_make_sync()`: one background event loop for the session, and every MCP call goes through
`asyncio.run_coroutine_threadsafe(...).result()`.

This is the honest cost of the sync-runner decision, paid once, in one place. Worth showing on
camera — it's the kind of seam every real integration has.

## Talking points

1. `cp mcp.json.example mcp.json`, restart, and ask for the project motto — a tool that didn't
   exist in Part 17. (Set `command` to your Python path if bare `python` isn't on your PATH.)
2. Explain MCP in one line: a standard way for agents to borrow tools they didn't ship with.
3. Show the async/sync bug, then the bridge.
4. `pip install -e .` and run `deepcoder` from your home directory. It's a real tool now.

## Run it

```bash
cd deepcoding_agent/18-mcp-packaging
python main.py
```

```bash
pip install -e . && deepcoder
```

For MCP: `cp mcp.json.example mcp.json` (needs `pip install langchain-mcp-adapters mcp`).

## Files in this snapshot

| File                    | Role                                                 |
| ----------------------- | ---------------------------------------------------- |
| `mcp_tools.py`          | Loads MCP servers; bridges async tools to sync       |
| `example_mcp_server.py` | A 15-line demo server so you can try MCP immediately |
| `pyproject.toml`        | Dependencies + the `deepcoder` entry point           |

## Where to take it next

1. **A sandbox backend** — swap `LocalShellBackend` for a Docker or LangSmith sandbox and the
   safety story changes completely.
2. **Better context management** — add `SummarizationMiddleware` for very long sessions.
3. **Real MCP servers** — GitHub, Postgres, Playwright. Your agent gets their tools for free.
4. **Per-subagent models** — a cheap model for review, an expensive one for writing code.
5. **Structured output** — `response_format=` for machine-readable results.

## Verify without a live model

```bash
python -m compileall -q . && ruff check .
python -m pytest test_smoke.py -q -p anyio
```
