# Episode 2 — The Agentic Loop: Making the Brain Think

## Overview
**Length:** ~15 minutes  
**Goal:** Add a custom tool to the agent and make the full reasoning loop visible through live streaming output.

## What You'll Learn
- **Tool registration**: How `@tool` decorator turns a Python function into an LLM-callable tool
- **Docstrings as prompts**: The model reads your docstring to decide when to call the tool — write them for the AI, not just humans
- **Streaming driver**: Using `agent.stream()` with LangGraph's v2 event format to print each node's output live
- **Thread state management**: Configuring thread IDs and recursion limits via the config dict

## Key Concepts
1. A tool is a function whose docstring tells the model *when* and *why* to call it — treat docstrings as part of your prompt engineering
2. `create_deep_agent` accepts `tools=[...]` to register custom tools alongside built-in ones
3. Streaming with `.stream(config, stream_mode="updates")` gives you visibility into each step: tool calls, results, and final responses
4. The agent loop is: receive user message → model decides action → call tool(s) → observe result → repeat until done

## Run Instructions
```bash
LLM_PROVIDER=ollama python 02-agentic-loop.py "What time is it?"
# Or with OpenAI:
LLM_PROVIDER=openai OPENAI_API_KEY=your-key LLM_MODEL=gpt-4o-mini \
    python 02-agentic-loop.py "What time is it?"
```

## Prerequisites
```bash
pip install deepagents langchain-ollama rich python-dotenv
```