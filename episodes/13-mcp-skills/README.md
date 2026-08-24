# Episode 13 — MCP + Skills: Speaking the Standard Protocol

## Overview

**Length:** ~40 minutes  
**Goal:** Extend the agent with two ecosystem capabilities: connect to external tools via the Model Context Protocol (MCP), and load reusable skill definitions from a `skills/` directory.

## What You'll Learn

- **MCP integration**: Using `langchain-mcp-adapters` to connect to an MCP server and register its tools alongside custom ones — fully automatic exposure
- **`build_mcp_config()` + `load_mcp_tools()`**: Async helpers that discover and load tools from a configured MCP server URL
- **Skills system**: A `skills/` directory with `SKILL.md` files (YAML frontmatter + markdown instructions) loaded by Deep Agents' built-in `SkillsMiddleware` (#2 in the default stack) — progressive disclosure keeps context small until needed

## Key Concepts

1. MCP is a standard protocol for connecting tools to LLMs — any MCP-compatible server can provide tools that your agent uses transparently
2. MCP tool loading is **async** (`get_tools()` is a coroutine) — use `asyncio.run()` to load before calling `build_agent`
3. Skills are markdown files with structured frontmatter; the middleware loads summaries at startup and fetches full instructions on demand, keeping context lean
4. Both capabilities are **optional**: if no MCP server is configured or it's down, `load_mcp_tools` returns `[]`; if no skills directory exists, `SkillsMiddleware` skips gracefully

## Run Instructions

```bash
# Create workspace:
mkdir -p ./workspace

# Start an MCP filesystem server (in a separate terminal):
npx @modelcontextprotocol/server-filesystem ./workspace &

# Run with MCP tools enabled:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 13-mcp-skills.py "List files in the workspace using MCP tools." --mcp-server-url http://localhost:3000/sse

# Or check available options:
python 13-mcp-skills.py --help
```

## Prerequisites

```bash
pip install deepagents langchain-ollama rich python-dotenv langchain-mcp-adapters
```
