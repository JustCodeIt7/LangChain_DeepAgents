"""
20 - MCP Tools (Connecting to the Outside World)
================================================
- MCP (Model Context Protocol) is a standard way to expose tools to any agent
- `MultiServerMCPClient` fetches those tools; deepagents treats them as normal tools
- NOTE: this episode is ASYNC — MCP clients are async, so we use `ainvoke`

Setup:  pip install langchain-mcp-adapters
Run:    python 20-mcp_tools.py
"""

# %% Step 1: Imports and setup
import asyncio
import os
import sys
from pathlib import Path

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")

# %% Step 2: Point at the MCP server
# mcp_server.py sits next to this file and exposes one tool: check_stock.
# We use an absolute path and the CURRENT interpreter (sys.executable) so the
# subprocess starts correctly no matter which directory you run this from.
SERVER_SCRIPT = Path(__file__).parent / "mcp_server.py"

server_config = {
    "inventory": {
        "transport": "stdio",  # launch the server as a subprocess and talk over pipes
        "command": sys.executable,
        "args": [str(SERVER_SCRIPT)],
    }
    # An HTTP server would look like:
    #   {"transport": "http", "url": "https://example.com/mcp"}
}


def text_of(message) -> str:
    """Normalize message content across providers (str vs content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 3: Everything MCP is async, so the work happens in a coroutine
async def main() -> None:
    """Fetch tools over MCP and hand them to a deep agent."""
    client = MultiServerMCPClient(server_config)

    # get_tools() starts the server and asks it what it can do. The result is a
    # list of ordinary LangChain tools — nothing deepagents-specific about them.
    tools = await client.get_tools()

    print("[bold cyan]Tools discovered over MCP:[/bold cyan]")
    for mcp_tool in tools:
        print(f"  [green]{mcp_tool.name}[/green] — {mcp_tool.description.splitlines()[0]}")

    # %% Step 4: Same create_deep_agent call as always
    # MCP tools go in `tools=` exactly like the hand-written ones from ep. 03.
    agent = create_deep_agent(
        model=MODEL,
        tools=tools,
        system_prompt=(
            "You are an inventory assistant. Use the check_stock tool to answer "
            "stock questions. Report the numbers plainly."
        ),
    )

    # %% Step 5: Await the run (ainvoke, not invoke)
    question = "Do we have any widgets and gizmos in stock?"
    result = await agent.ainvoke({"messages": [{"role": "user", "content": question}]})

    print("\n[bold cyan]MCP tool calls:[/bold cyan]")
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []) or []:
            print(f"  [green]{call['name']}[/green]({call['args']})")

    print(f"\n[bold green]Final answer:[/bold green] {text_of(result['messages'][-1])}")


# %% Step 6: Drive the event loop
asyncio.run(main())

# %%
