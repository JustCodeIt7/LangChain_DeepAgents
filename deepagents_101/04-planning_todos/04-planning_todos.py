"""
04 - Planning with Todos (TodoListMiddleware)
=============================================
- In deepagents 0.7 task planning is OPT-IN: add `TodoListMiddleware()`
- That gives the agent a `write_todos` tool for multi-step work
- Watch the plan evolve live with `stream(stream_mode="updates")`

Run:  python 04-planning_todos.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware  # supplies write_todos
from rich import print

load_dotenv()
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")

# %% Step 2: Opt in to planning
# Without this middleware there is no write_todos tool at all. (In deepagents
# 0.6 it was on by default; 0.7 made it explicit so simple agents stay lean.)
agent = create_deep_agent(
    model=MODEL,
    middleware=[TodoListMiddleware()],
    system_prompt=(
        "You are a careful planner. For any multi-step request, FIRST call "
        "write_todos to lay out the steps, update it as you go, then give the "
        "final answer in a separate message."
    ),
)

# %% Step 3: Give it work that deserves a plan
# Three distinct steps is the sweet spot — enough to justify planning,
# small enough to stay fast.
task = (
    "Do these three things: 1) compute 12 * 12, 2) reverse the word 'agents', "
    "3) give me both results in one final sentence."
)

# %% Step 4: Stream the run and watch the todo list change
# stream_mode="updates" yields one chunk per node that just ran, so we can see
# each write_todos call as it lands instead of waiting for the final state.
print("[bold cyan]Streaming updates:[/bold cyan]")
todo_snapshots = []
final_state = None

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": task}]}, stream_mode="updates"
):
    for node_name, update in chunk.items():
        if not isinstance(update, dict):
            continue
        # Todos live in state under the "todos" key once the tool is used.
        if "todos" in update:
            todo_snapshots.append(update["todos"])
            print(f"  [magenta]{node_name}[/magenta] updated the plan "
                  f"({len(update['todos'])} items)")
        for message in update.get("messages", []):
            for call in getattr(message, "tool_calls", []) or []:
                print(f"  [magenta]{node_name}[/magenta] called "
                      f"[green]{call['name']}[/green]")
        final_state = update

# %% Step 5: Show how the plan evolved
print(f"\n[bold cyan]The plan was revised {len(todo_snapshots)} time(s):[/bold cyan]")
for index, snapshot in enumerate(todo_snapshots, start=1):
    print(f"\n[bold]Revision {index}[/bold]")
    for todo in snapshot:
        # Note: square brackets are rich markup, so we use plain symbols here.
        marks = {"pending": "○", "in_progress": "◐", "completed": "●"}
        mark = marks.get(todo.get("status"), "○")
        print(f"  {mark} {todo.get('content')}")

if not todo_snapshots:
    print("  [yellow]The model answered without planning — try a longer task.[/yellow]")

# %%
