# Episode 6 — Permission Gating: Human-in-the-Loop

## Overview
**Length:** ~25 minutes  
**Goal:** Add a human approval gate so the agent must ask before executing destructive tools (shell commands, file writes). Uses Deep Agents' built-in `HumanInTheLoopMiddleware`.

## What You'll Learn
- **Interrupt/resume pattern**: How to pause the graph when a gated tool is called, prompt the user for y/n, and resume with `Command(resume=...)`
- **`classify(command)`**: A regex-based risk triage function that labels commands as red/yellow/green so viewers see danger at a glance
- **`run_with_approval()`**: The full interrupt/resume loop — invoke → check if paused → ask viewer → resume → repeat

## Key Concepts
1. `create_deep_agent(interrupt_on=[...], checkpointer=...)` configures which tools trigger an interruption before execution
2. When the model calls a gated tool, the graph pauses and returns control to your CLI code via `.invoke()` or streaming events
3. You inspect state with `agent.get_state(config)`, prompt the user for approval, then resume using `Command(resume={"decisions": [...]})` passed back into the agent
4. The approval gate is essential before giving an agent shell access — it prevents accidental destruction of files or system resources

## Run Instructions
```bash
# Create workspace if needed:
mkdir -p ./workspace && echo "print('hello')" > ./workspace/test.py

# Ask the agent to create then delete a file (approval will be requested):
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 06-approval-gate.py "Create a file called notes.txt with 'hello world', then delete it."

# You'll be prompted y/n before each destructive action.
```

## Prerequisites
```bash
pip install deepagents langchain-ollama rich python-dotenv
```