"""
Optional MCP tools.
===================
The Model Context Protocol is how agents borrow tools they did not ship with:
GitHub, Postgres, Playwright, your company's internal server. Drop an
mcp.json next to main.py and every tool those servers expose joins DeepCoder's
toolbox.

  {"mcpServers": {"docs": {"command": "python", "args": ["my_server.py"]}}}
"""

import asyncio
import json
import threading
from pathlib import Path

from langchain_core.tools import StructuredTool

CONFIG_FILE = Path(__file__).parent / "mcp.json"

# One background event loop, alive for the whole session. MCP tools are
# async-only, but DeepCoder's runner is deliberately synchronous, so every
# MCP call is handed to this loop and waited on.
_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True).start()


def _make_sync(tool: StructuredTool) -> StructuredTool:
    """Give an async-only tool a synchronous front door.

    Without this the agent raises "StructuredTool does not support sync
    invocation" the first time the model picks an MCP tool -- the tool loads
    fine, then explodes at call time.
    """

    def call_it(*args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(tool.coroutine(*args, **kwargs), _loop)
        return future.result()

    return StructuredTool(
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
        func=call_it,
        coroutine=tool.coroutine,  # keep the async path for async callers
    )


def load_tools() -> list:
    """Return the MCP tools, or [] when there is nothing configured.

    MCP clients are async-only, but DeepCoder is a synchronous app. We resolve
    that with asyncio.run() ONCE at startup, before Textual owns the event
    loop -- never from inside a running app, where two loops would collide.
    """
    if not CONFIG_FILE.exists():
        return []

    try:
        servers = json.loads(CONFIG_FILE.read_text()).get("mcpServers", {})
    except json.JSONDecodeError as error:
        print(f"mcp.json is not valid JSON: {error}")
        return []
    if not servers:
        return []

    # langchain-mcp-adapters wants "transport" spelled out per server.
    connections = {
        name: {**spec, "transport": spec.get("transport", "stdio")}
        for name, spec in servers.items()
    }

    async def fetch() -> list:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        return await MultiServerMCPClient(connections).get_tools()

    try:
        tools = asyncio.run(fetch())
    except Exception as error:  # noqa: BLE001 - a bad server must not stop startup
        print(f"MCP servers unavailable ({error}); continuing without them.")
        return []

    print(f"MCP: loaded {len(tools)} tool(s) from {', '.join(connections)}")
    return [_make_sync(tool) if tool.func is None else tool for tool in tools]
