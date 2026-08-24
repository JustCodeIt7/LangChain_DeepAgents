"""
19 - Capstone: A Research Agent
===============================
Everything from the series in one agent:
- planning (ep. 04) + virtual filesystem (ep. 05)
- a specialist subagent (ep. 09) + live streaming (ep. 17)
- It researches a local corpus and writes a report file. No internet required.

Run:  python 19-capstone_research.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.utils import create_file_data
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")

# %% Step 2: The corpus — the agent's "world"
# In a real research agent these would be web pages or PDFs. Keeping them local
# makes the episode fast, free, and reproducible.
CORPUS = {
    "/corpus/solar.md": (
        "# Solar\n"
        "Solar panel costs fell about 90% between 2010 and 2024.\n"
        "Solar is now the cheapest source of new electricity in most countries.\n"
        "Its main drawback is intermittency: no output at night.\n"
    ),
    "/corpus/wind.md": (
        "# Wind\n"
        "Offshore wind turbines have grown to over 250m tall.\n"
        "Wind often generates most strongly at night, complementing solar.\n"
        "Its main drawback is the high upfront cost of offshore installation.\n"
    ),
    "/corpus/storage.md": (
        "# Storage\n"
        "Grid battery costs fell roughly 80% in the last decade.\n"
        "Storage is the key technology for smoothing solar and wind intermittency.\n"
    ),
}
seed_files = {path: create_file_data(text) for path, text in CORPUS.items()}

# %% Step 3: A specialist subagent
# It reads one source and reports back. Because subagents have isolated context
# (ep. 09), the long file contents never clog the orchestrator's history —
# only the short summary comes back.
analyst = {
    "name": "analyst",
    "description": (
        "Reads ONE file from /corpus/ and returns 2-3 bullet points of key facts. "
        "Use once per source file."
    ),
    "system_prompt": (
        "You are a research analyst. Use read_file on the path you are given, "
        "then reply with 2-3 concise bullet points of the key facts. Nothing else."
    ),
}

# %% Step 4: Assemble the full agent
agent = create_deep_agent(
    model=MODEL,
    backend=StateBackend(),
    middleware=[TodoListMiddleware()],  # planning, from ep. 04
    subagents=[analyst],  # delegation, from ep. 09
    system_prompt=(
        "You are a research lead. Workflow: "
        "1) call write_todos to plan, "
        "2) use ls to see what is in /corpus/, "
        "3) delegate EACH source file to the 'analyst' subagent with the task tool, "
        "4) write_file a synthesis to /report.md with a '# Report' heading, "
        "a short paragraph, and a 'Sources' list. "
        "Then reply with one sentence confirming the report is written."
    ),
)

# %% Step 5: Run it, streaming progress as it works
brief = (
    "Research how solar, wind, and storage fit together as a renewable energy "
    "system, then write the report to /report.md."
)

print("[bold cyan]Working:[/bold cyan]")
final_state = None
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": brief}], "files": seed_files},
    stream_mode="values",  # "values" gives the full state each step, so we can grab files
):
    final_state = chunk
    last = chunk["messages"][-1] if chunk.get("messages") else None
    for call in getattr(last, "tool_calls", []) or []:
        target = call["args"].get("file_path") or call["args"].get("subagent_type") or ""
        print(f"  [magenta]{call['name']}[/magenta] [yellow]{target}[/yellow]")

# %% Step 6: The deliverable
print("\n[bold cyan]Files at the end of the run:[/bold cyan]")
print(f"  {sorted(final_state['files'].keys())}")

report = final_state["files"].get("/report.md")
print("\n[bold green]/report.md[/bold green]")
print(report["content"] if report else "[red]The agent did not write a report.[/red]")

# %%
