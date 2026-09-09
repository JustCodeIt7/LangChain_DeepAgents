"""
A tiny MCP server so you can try MCP immediately.
=================================================
Copy mcp.json.example to mcp.json; DeepCoder starts this as a subprocess.
You never run it yourself.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("deepcoder-demo")


@mcp.tool()
def project_motto() -> str:
    """Return this project's official motto."""
    return "Ship small parts, verify each one."


if __name__ == "__main__":
    mcp.run(transport="stdio")
