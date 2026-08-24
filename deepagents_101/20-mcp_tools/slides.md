---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 20 — MCP Tools

*A standard way to expose tools to any agent — and to deepagents they are just tools*

---

# Point at a Server, Fetch Its Tools

```python
server_config = {
    "inventory": {
        "transport": "stdio",          # launch as a subprocess, talk over pipes
        "command": sys.executable,     # the CURRENT interpreter
        "args": [str(SERVER_SCRIPT)],  # an ABSOLUTE path
    }
    # HTTP instead: {"transport": "http", "url": "https://example.com/mcp"}
}

client = MultiServerMCPClient(server_config)
tools = await client.get_tools()      # starts the server, asks what it can do
```

- `get_tools()` returns **ordinary LangChain tools** — nothing deepagents-specific about them

---

# Same Agent, Async Run

```python
agent = create_deep_agent(model=MODEL, tools=tools)   # exactly like ep. 03
result = await agent.ainvoke({"messages": [...]})     # ainvoke, not invoke
```

- MCP tools go in `tools=` alongside your hand-written ones — **additive as ever**
- ⚠️ MCP clients are **async**, so the whole episode lives in a coroutine driven by `asyncio.run(main())`
- `sys.executable` + an absolute script path make the subprocess start from **any** working directory

**That's the series.** You now have the whole deepagents surface — go build something.
