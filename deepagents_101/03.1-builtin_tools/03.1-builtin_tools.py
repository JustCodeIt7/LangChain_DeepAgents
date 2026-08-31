"""
03 - Built-in Tools
===================
Deep Agents supplies filesystem tools and a `task` subagent tool automatically.
`LocalShellBackend` also exposes `execute`; TodoListMiddleware opts into
`write_todos`. This demo makes every tool act in a disposable lesson workspace.

Run: python 03-builtin_tools-cx.py
Override: DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 03-builtin_tools-cx.py
"""

# %% Step 1: Imports and model configuration
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware
from langchain_ollama import ChatOllama
from rich import print

################################ Environment & Model Configuration ################################

# Pull API keys and model overrides from a local .env file
load_dotenv()

# Allow the model to be swapped without editing code; fall back to a small local Ollama model
# openai
MODEL = "openai:gpt-4.1-nano"  # gpt-4.1-nano
# ollama
OLLANMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# llama3.2 granite4:1b qwen3.5:2b
MODEL = ChatOllama(model="granite4:1b", base_url=OLLANMA_BASE_URL, temperature=0)

# Sandbox directory that every tool call is confined to
WORKSPACE = Path(__file__).parent / "workspace"

# Checklist used at the end to verify which built-in tools the agent actually exercised
BUILT_INS = (
    "write_todos",
    "ls",
    "read_file",
    "write_file",
    "edit_file",
    "glob",
    "grep",
    "execute",
    "task",
    "delete",
)
# print(MODEL)

# %% Step 2: Create safe, repeatable data for the agent to explore
def seed_workspace() -> None:
    """Reset only this tutorial's sample files before each run."""
    # Recreate the data folder so reruns always start from a known state
    data = WORKSPACE / "data"
    data.mkdir(parents=True, exist_ok=True)
    # Create initial sample files for the agent to interact with
    (data / "fruits.txt").write_text("apple\nbanana\ncherry\n")
    (data / "colors.txt").write_text("red\nblue\ngreen\n")
    # Create a notes file for the agent to edit
    (WORKSPACE / "notes.md").write_text("# Notes\n- status: draft\n")
    # Ensure the veggies file is initially absent so the agent can create it
    (data / "veggies.txt").unlink(missing_ok=True)  # Clear the file the agent is asked to create


# %% Step 3: Build an agent with every available harness tool
def build_agent():
    """LocalShellBackend adds execute; middleware adds write_todos."""
    # Jail shell + filesystem access to the workspace and cap runaway commands
    backend = LocalShellBackend(root_dir=str(WORKSPACE.resolve()), timeout=30)
    return create_deep_agent(
        model=MODEL,
        backend=backend,
        middleware=[TodoListMiddleware()],  # Opt in to the write_todos planning tool
        # Force explicit tool usage so the demo can prove each tool works
        system_prompt="""You are demonstrating Deep Agents tools in a throwaway workspace.
            For every requested operation, call the named tool exactly; never replace a            filesystem operation with execute. Use relative paths. Keep final answers brief.
            workspace path is: ./ all file operations should be relative to this path.""",
    )


# %% Step 4: Short prompts that explicitly cover every tool
# Each prompt names the tools it should trigger, spreading coverage across turns
PROMPTS = [
    (  # tools: ls, read_file, write_todos
        "1. Use write_todos to plan these two items, then use ls on data and "
        "read_file on data/fruits.txt and tell me what fruits are listed."
    ),
    (  # tools: edit_file, write_file
        "2. Use write_file to create data/veggies.txt containing carrot, pepper, and basil on separate lines."
        "Then use edit_file to change 'draft' to 'final' in notes.md."
    ),
    (  # tools: glob, grep, execute
        "3. Use glob to find every .txt file. Use grep to find the file containing 'blue'. "
        "Use execute to run exactly: wc -l data/*.txt"
    ),
    (  # tools: task, delete, write_todos
        "4. Use task to delegate counting all lines in data/*.txt to a subagent."
        "Then use the delete tool to remove data/veggies.txt, complete the todos, and summarize the results."
    ),  # delete
    ("5. use delete tool to remove a file from the workspace"),
    (
        "6. List all built-in tools available to you in deepagents with a brief description of each, and write each "
        "tool's name and description to a markdown file named todo.md in the workspace directory using the write_file "
        "or edit_file tool."
    ),
]


def tool_names(messages: list) -> set[str]:
    """Collect tool names from the agent's LangChain messages."""
    # Flatten tool_calls across all messages; plain text messages simply contribute nothing
    tool_names = set()
    # Iterate over all messages and collect the names of tools that were called
    for message in messages:
        # Skip messages that have no tool calls (i.e., "tool_calls" attribute is missing or empty)
        for call in getattr(message, "tool_calls", []) or []:
            tool_names.add(call["name"])
    # Return the collected set of tool names
    return tool_names


# %% Step 5: Run the guided conversation and report actual coverage
def main() -> None:
    """Invoke each prompt, preserving messages so the agent can continue its plan."""
    seed_workspace()
    # Initialize the agent, message history, and set of called tools
    agent, messages, called = build_agent(), [], set()
    print(f"[dim]model: {MODEL}  workspace: {WORKSPACE}[/dim]")

    # Replay the full history each turn so the agent keeps its todo list context
    for turn, prompt in enumerate(PROMPTS, start=1):
        print(f"\n[bold magenta]--- Turn {turn} ---[/bold magenta]")
        # Invoke the agent with the current prompt and the accumulated message history
        result = agent.invoke({"messages": messages + [{"role": "user", "content": prompt}]})
        print("Got results finding new tool calls...")
        # Update the message history and determine which tools were newly called this turn
        messages = result["messages"]
        tools_used = tool_names(messages)
        # Determine which tools were newly called this turn
        new_calls = tools_used - called  # Report only tools first seen this turn

        called.update(new_calls)
        print("tools used:", ", ".join(sorted(tools_used)) or "none")
        print("  answer: \n")
        print(messages[-1])

    # Score the run against the expected built-in tool list
    print("\n[bold cyan]Built-in tool coverage[/bold cyan]")
    for name in BUILT_INS:
        # Check if the current built-in tool was called during the conversation
        marker = "[green]yes[/green]" if name in called else "[red]no[/red]"
        print(f"  {name:11} {marker}")  # Pad names so the yes/no column lines up
    print(f"\n[bold green]Final answer:[/bold green] {messages[-1].text}")


# Run the demo only when executed directly, not on import
if __name__ == "__main__":
    main()
