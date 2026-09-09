"""A tiny MCP server used by episode 20.

Run by the episode script as a subprocess over stdio — you do not start it
yourself. Any MCP client (Claude Desktop, an IDE, another agent) could use it too.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("inventory")


@mcp.tool()
def check_stock(product: str) -> str:
    """Check how many units of a product are currently in stock.

    Args:
        product: The product name to look up.
    """
    inventory = {"widget": 42, "gizmo": 0, "doohickey": 7}
    key = product.lower().strip().rstrip("s")  # tolerate "widgets" as well as "widget"
    count = inventory.get(key)
    if count is None:
        return f"'{product}' is not a product we carry."
    return f"{product}: {count} units in stock"


if __name__ == "__main__":
    mcp.run(transport="stdio")
