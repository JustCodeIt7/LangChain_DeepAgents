"""
03 - Built-in Tools: A Complete Deep Agent Workspace
=====================================================
- LocalShellBackend is real host shell access: this demo is scoped to ./workspace.
Run:  python 03-builtin_tools-cxv2.py
"""
# %% Step 1: Imports and a tightly scoped workspace
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware
from rich import print

from langchain_ollama import ChatOllama
from langchain_openrouter import ChatOpenRouter
load_dotenv()


# Choose your LLM provider by commenting/uncommenting:
#
# Option 1: Ollama (local)
# Make sure Ollama is running and you have pulled the model (e.g., ollama pull qwen3.5:2b)
model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "qwen3.5:2b"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
)
#
# Option 2: OpenRouter
# model = ChatOpenRouter(
#     model="meta/muse-spark-1.3-contributor",
#     temperature=0
# )

# %% Step 2: Prompts that exercise the full built-in tool suite
PROMPTS = [
    (
        "Plan, write, list, and read",
        "First use write_todos for: create and verify a note. Then use write_file to "
        "create /notes.md containing exactly 'the brown fox', use ls to list /, and "
        "use read_file to verify /notes.md. Do each step.",
    ),
    (
        "Edit, glob, and grep",
        "Use edit_file to replace 'brown' with 'swift' in /notes.md. Then use glob to "
        "find Markdown files and grep to find 'swift' in /notes.md. Do not skip tools.",
    ),
    (
        "Delegate",
        "Use the built-in task tool to delegate to the reporter subagent. Ask it to "
        "reply with its fixed confirmation. Do no other work.",
    ),
    (
        "Execute and delete",
        'Use execute to run exactly: python -c "from pathlib import Path; '
        "print(Path('notes.md').read_text().upper())\". Then use delete to remove "
        "/notes.md. Do not run any other command.",
    ),
]
EXPECTED = {
    "write_todos", "write_file", "ls", "read_file", "edit_file", "glob", "grep",
    "task", "execute", "delete",
}
used_tools = set()
for number, (title, prompt) in enumerate(PROMPTS, start=1):
    print(f"\n[bold cyan]{number}. {title}[/bold cyan]")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={"recursion_limit": 12, "configurable": {"thread_id": f"builtins-{number}"}},
        )
    except Exception as error:
        print(f"  [red]Prompt failed: {error}[/red]")
        continue
    calls = {
        call["name"] for message in result["messages"]
        for call in (getattr(message, "tool_calls", []) or [])
    }
    used_tools.update(calls)
    print(f"  tools: [green]{', '.join(sorted(calls))}[/green]")
    print(f"  answer: {result['messages'][-1].content}")

# %% Step 4: Report whether this model followed every tool-specific prompt
missing = EXPECTED - used_tools
status = "all built-in tools exercised" if not missing else f"missing: {', '.join(sorted(missing))}"
print(f"\n[bold cyan]Coverage:[/bold cyan] [yellow]{status}[/yellow]")
# %%