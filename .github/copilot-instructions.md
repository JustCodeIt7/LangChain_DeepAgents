# LangChain Deep Agents - AI Coding Agent Instructions

## Project Overview

YouTube tutorial series demonstrating LangChain's `deepagents` package for building multi-step AI agents with planning, file systems, and subagent capabilities. Code examples use local Ollama models + Tavily search, designed to be under 100 lines and YouTube-friendly.

## Architecture & Key Components

### Core Pattern: Deep Agent Structure

All examples follow this pattern from `01-Intro/01-intro.py`:

1. **LLM Setup**: Ollama (local, free) as primary, OpenAI as commented alternative
2. **Tool Definition**: Functions decorated for agent use (e.g., `internet_search`)
3. **Agent Creation**: `create_deep_agent(model, tools, system_prompt)`
4. **Execution & Logging**: `agent.invoke()` → `print_agent_execution()` → `save_agent_result()`

```python
# Standard agent initialization pattern
model = ChatOllama(model="gpt-oss:20b", base_url=OLLAMA_BASE_URL)
agent = create_deep_agent(model=model, tools=[internet_search], system_prompt=instructions)
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

### Utilities Architecture (`utils.py`)

Three core functions for agent observability:

- `print_agent_execution(result, max_length=500)`: Shows message-by-message trace with emojis (👤 human, 🤖 ai, 🔧 tool). AI messages with tool calls display: `[AI] - Calling: tool_name`
- `print_agent_summary(result)`: Counts messages, tool calls, results
- `save_agent_result(result, filename)`: Serializes LangChain message objects to JSON

## Development Workflow

### Environment Setup

```bash
# 1. Activate conda environment (project uses py312)
conda activate /Users/james/miniconda3/envs/py312

# 2. Install core dependencies (no requirements.txt yet)
pip install deepagents langchain-ollama langchain-openai tavily-python python-dotenv rich

# 3. Ensure .env exists with keys (never commit)
# OLLAMA_BASE_URL=http://localhost:11434
# TAVILY_API_KEY=your_key
# OPENAI_API_KEY=your_key  # optional
```

### Running Examples

```bash
# Primary tutorial - full featured
python 01-Intro/01-intro.py

# Minimal variant (smaller model)
python "01-Intro/01-intro copy.py"
```

### Prerequisites Before Running

1. **Ollama must be running locally** and model must be pulled:
   ```bash
   ollama pull gpt-oss:20b  # or llama3.2, qwen3:1.7b
   ```
2. **Tavily API key** set in `.env`
3. Conda environment activated

## Project-Specific Conventions

### Code Organization

- **Tutorial structure**: Each numbered folder (e.g., `01-Intro/`) contains complete, standalone examples
- **File naming**: Main tutorial uses folder name (`01-intro.py`), variants use `copy` suffix
- **Cell markers**: Use `# %%` for VS Code/Jupyter cell boundaries - enables step-by-step execution
- **Imports pattern**: Always add parent to path for utils: `sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`

### LLM Configuration

- **Default**: `ChatOllama(model="gpt-oss:20b", base_url=OLLAMA_BASE_URL)` - uses env var
- **Alternative**: Commented OpenAI blocks ready to uncomment
- **Never hardcode**: Model names, base URLs, API keys - always use env vars or function params

### Deep Agent System Prompts

Keep under 10 lines, specify:

1. Agent role (e.g., "expert researcher")
2. Available tools and when to use them
3. Output format/structure
4. Key behavior (e.g., "cite sources")

Example from `01-intro.py`:

```python
research_instructions = """You are an expert researcher and writer.

Your job is to:
1. Conduct thorough research using the internet_search tool
2. Break down complex tasks into manageable steps
3. Organize your findings clearly
4. Write a concise, informative report

Always cite your sources and be factual."""
```

### Tool Definition Pattern

```python
def tool_name(
    required_param: type,
    optional_param: type = default,
) -> dict:
    """Docstring becomes tool description for agent.

    Args:
        param: Description (agent sees this)
    """
    # Use external client (Tavily, etc.)
    return client.method(...)
```

### Output & Logging

- **Console**: Use `print_agent_execution()` for traces, shows tool calls inline
- **JSON**: Save results to folder: `save_agent_result(result, "01-Intro/agent_response.json")`
- **Rich formatting**: `from rich import print` used in utils for enhanced output

## YouTube Tutorial Constraints

- **Code length**: Keep examples under 100 lines (excluding docstrings/comments)
- **Readability**: Use cell markers, clear variable names, emojis in output
- **Self-contained**: Each tutorial should run independently
- **Comments**: Over-explain for video clarity - every major step gets a `# Step N:` comment

## Integration Points

### External Dependencies

- **Ollama**: Local LLM backend - must be running before script execution
- **Tavily**: Web search API - requires `TAVILY_API_KEY` in `.env`
- **Optional OpenAI**: Swap in by uncommenting and setting `OPENAI_API_KEY`

### DeepAgents Middleware

Deep agents automatically include (no explicit config needed):

- **TodoListMiddleware**: Planning/task breakdown
- **FilesystemMiddleware**: Context management
- **SubAgentMiddleware**: Task delegation

Access via built-in tools: `write_todos`, `read_file`, `write_file`, etc.

## Common Patterns

### Adding a New Tutorial

1. Create folder: `02-Name/`
2. Copy `01-intro.py` structure (imports → LLM → tools → agent → run → log)
3. Define new tool functions with docstrings
4. Update system prompt for new use case
5. Keep under 100 lines
6. Add cell markers for step-by-step execution

### Debugging Agent Runs

```python
# 1. Check execution trace
print_agent_execution(result)  # Shows all messages + tool calls

# 2. Inspect raw messages
for msg in result["messages"]:
    print(f"{msg.type}: {msg.content[:100]}")

# 3. Save for offline analysis
save_agent_result(result, "debug_run.json")
```

### Swapping Models

```python
# Local Ollama (default)
model = ChatOllama(model="llama3.2", base_url=OLLAMA_BASE_URL)

# Hosted OpenAI (uncomment)
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini")

# Agent creation stays identical
agent = create_deep_agent(model=model, tools=[...], system_prompt=...)
```

## Key Files Reference

- `01-Intro/01-intro.py`: Main tutorial template (89 lines)
- `utils.py`: Observability helpers (114 lines total, 3 functions)
- `.env`: API keys (git-ignored, must create manually)
- `AGENTS.md`: High-level project docs for AI agents
- `README.md`: Human-readable setup guide
