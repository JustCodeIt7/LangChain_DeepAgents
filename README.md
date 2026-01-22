# LangChain Deep Agents Tutorials

Hands-on tutorials for building deep, multi-step agents with LangChain/LangGraph. The examples show how to combine local LLMs (Ollama), web search, and simple observability utilities to plan, execute, and review agent runs.

## What is inside

- `01-Intro/01-intro.py`: Research agent that uses Tavily web search, runs on an Ollama-hosted model, and logs execution traces. Demonstrates planning, tool use, and report generation.
- `01-Intro/01-intro copy.py`: Minimal variant that wires a small Ollama model and Tavily search to answer a single question.
- `01-Intro/agent_response.json`: Sample output produced by the intro script.
- `utils.py`: Helper functions to pretty-print agent traces, summarize runs, and save JSON responses.
- `result.csv`: Preserved experiment output (not used by the intro scripts but kept for reference).

## Prerequisites

- Python 3.12+
- pip and a virtual environment tool (`python -m venv` recommended)
- Ollama running locally (`OLLAMA_BASE_URL` defaults to `http://localhost:11434`). Pull a model such as `gpt-oss:20b` or `llama3.2` before running: `ollama pull gpt-oss:20b`.
- Tavily API key for web search.
- Optional: OpenAI API key if you want to swap in `gpt-4.1-nano` or another hosted model.

## Setup

1. Clone the repo and create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

2. Install dependencies (once `requirements.txt` is present)

```bash
pip install -r requirements.txt
```

If you do not have a requirements file yet, install the core libs directly:

```bash
pip install deepagents langchain-ollama langchain-openai tavily-python python-dotenv rich
```

3. Create a `.env` file for secrets and configuration (do not commit it)

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
TAVILY_API_KEY=your_tavily_key
# Optional when using hosted models
OPENAI_API_KEY=your_openai_key
```

## Running the intro tutorial

1. Ensure Ollama is running and the chosen model is pulled.
2. Ensure `TAVILY_API_KEY` is set in `.env`.
3. Run the script:

```bash
python 01-Intro/01-intro.py
```

What it does:

- Loads environment variables from `.env`.
- Starts an Ollama-backed chat model (`gpt-oss:20b` by default; adjust in the script if you prefer another model).
- Registers a Tavily-powered `internet_search` tool and builds a deep agent via `create_deep_agent` with research instructions.
- Invokes the agent to research LangGraph, prints a detailed execution trace, prints a summary, and can save the response to `01-Intro/agent_response.json` via the utilities.

## Minimal variant

`python "01-Intro/01-intro copy.py"` wires a lightweight Ollama model (`ollama:qwen3:1.7b`) with Tavily search to answer a single question. Use this when you want the smallest possible local model footprint.

## Utilities

`utils.py` exposes small helpers you can reuse in additional tutorials:

```python
from utils import print_agent_execution, print_agent_summary, save_agent_result

result = agent.invoke({"messages": [{"role": "user", "content": "Research ..."}]})
print_agent_execution(result)              # Message-by-message trace with emojis
print_agent_execution(result, max_length=200)  # Truncate long messages
print_agent_summary(result)                # Quick counts of messages and tool calls
save_agent_result(result, "output.json")   # Persist run output as JSON
```

The execution trace shows:
- 👤 Human messages (user input)
- 🤖 AI messages (agent responses and tool calls)
- 🔧 Tool messages (tool results)

AI messages with tool calls display: `[AI] - Calling: tool_name`

## AI Coding Agent Support

This project includes comprehensive instructions for AI coding agents (GitHub Copilot, Cursor, Windsurf, etc.) in `.github/copilot-instructions.md`. The instructions cover:

- Project architecture and deep agent patterns
- Development workflow (conda environment, Ollama setup)
- Project-specific conventions (cell markers, imports, system prompts)
- YouTube tutorial constraints (<100 lines per example)
- Common patterns for debugging and adding new tutorials

AI agents using these instructions will understand the project structure and coding conventions immediately.

## Tips

- Keep secrets in `.env`; never commit keys.
- Swap the model by changing `ChatOllama(model=...)` or uncommenting the `ChatOpenAI` lines in `01-Intro/01-intro.py`.
- If you add new examples, follow the pattern in `01-Intro/01-intro.py`: define tools, craft a clear system prompt, and log the run with the provided utilities.
- Use `# %%` cell markers for step-by-step execution in VS Code or Jupyter.
- For local development, this project uses conda environment `py312`: `conda activate /Users/james/miniconda3/envs/py312`
