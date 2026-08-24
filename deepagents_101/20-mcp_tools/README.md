# 20 — MCP Tools (Connecting to the Outside World)

## Overview

**Goal:** Fetch tools from an MCP (Model Context Protocol) server with `MultiServerMCPClient` and hand them to a deep agent exactly like hand-written tools.

## What You'll Learn

- **Server config**: `{"inventory": {"transport": "stdio", "command": sys.executable, "args": [str(SERVER_SCRIPT)]}}` launches the bundled `mcp_server.py` as a subprocess and talks over pipes; an HTTP server would be `{"transport": "http", "url": "..."}`
- **`await client.get_tools()`**: starts the server and returns a list of ordinary LangChain tools — nothing deepagents-specific about them
- **Same `create_deep_agent` call as always**: MCP tools go in `tools=` just like the hand-written ones from ep. 03
- **Everything MCP is async**: the episode uses `ainvoke`, not `invoke`

## Key Concepts

1. `sys.executable` + an absolute script path means the subprocess starts correctly no matter which directory you run the episode from
2. MCP is a standard: the same `mcp_server.py` could be used by Claude Desktop, an IDE, or another agent
3. The bundled server exposes one tool, `check_stock`, over a tiny in-memory inventory

## Teaching Notes

**Hook:** "MCP is a standard way to expose tools to any agent — deepagents treats them as normal tools."

**Walk the cells:**

- **Step 2 — Point at the server:** `{"inventory": {"transport": "stdio", "command": sys.executable, "args": [str(SERVER_SCRIPT)]}}` launches `mcp_server.py` as a subprocess. The HTTP alternative is in the comments.
- **Step 3 — Everything MCP is async:** The work happens in a coroutine; `get_tools()` starts the server and returns ordinary LangChain tools.
- **Step 4 — Same create_deep_agent call:** MCP tools go in `tools=` exactly like the hand-written ones from ep. 03.
- **Step 5 — Await the run:** `ainvoke`, not `invoke`.

**On camera:**

- The "Tools discovered over MCP" list is the payoff — the agent found a tool it was never told about, over a wire protocol.

**If it goes wrong:**

- The only episode needing an extra dependency (`langchain-mcp-adapters`). If the subprocess doesn't start, check the path and interpreter.

**Bridge (series finale):** Recap the arc — from one function call (ep. 01) to an agent that plans, works on files, delegates, remembers, and now pulls tools from the outside world.

## Slides & Diagrams

- `slides.md` — 3-slide Marp deck overview of the episode. Preview with the Marp VS Code extension or `npx @marp-team/marp-cli slides.md`
- `diagrams/` — Mermaid sources (`.mmd`) with rendered `.svg`/`.png`: MCP client, transports, async flow

## Run Instructions

```bash
cd deepagents_101/20-mcp_tools
python 20-mcp_tools.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 20-mcp_tools.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).

## Notes

- **Only episode needing an extra dependency**: `pip install langchain-mcp-adapters`
- `mcp_server.py` is run by the episode as a subprocess — you do not start it yourself.
