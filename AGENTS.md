# AGENTS.md

## Project overview

Tutorials for building deep, multi-step agents using LangChain and LangGraph. The examples are used in accompanying YouTube videos and focus on local-first workflows with Ollama plus lightweight observability utilities.

## Preferences and dependencies

1. Python 3.12 or later
2. Install dependencies with pip (after `python -m venv .venv && source .venv/bin/activate`):

    ```bash
    pip install -r requirements.txt
    # If requirements.txt is missing, install the core libs:
    pip install deepagents langchain-ollama langchain-openai tavily python-dotenv
    ```

3. Configuration via `.env` (never commit):

    ```dotenv
    OLLAMA_BASE_URL=http://localhost:11434
    TAVILY_API_KEY=your_tavily_key
    # Optional for hosted models
    OPENAI_API_KEY=your_openai_key
    ```

4. Default LLM backend: Ollama

   ```python
   from langchain_ollama import ChatOllama, OllamaEmbeddings
   from langchain_openai import ChatOpenAI

   llm = ChatOllama(model="gpt-oss:20b", base_url=OLLAMA_BASE_URL)
   embedding = OllamaEmbeddings(model="nomic-embed-text")

   # Optional hosted model
   llm = ChatOpenAI(model="gpt-4.1-nano", max_tokens=500)
   ```

5. Do not make the code too complex; keep it simple and focused on demonstrating deep agent capabilities.

6. Always load secrets from `.env` using `python-dotenv`.

7. Use rich print statements for better console output.

    ``` python
    from rich import print
    print("Hello, [bold magenta]World[/bold magenta]!")
    ```


## Project structure

- `01-Intro/01-intro.py`: Main tutorial showing a research agent that uses Tavily web search, planning, and trace logging.
- `01-Intro/01-intro copy.py`: Minimal variant wiring a small Ollama model and Tavily search for a single question.
- `01-Intro/agent_response.json`: Sample output from the intro run.
- `utils.py`: Helpers to print execution traces, summarize runs, and save JSON results.
- `README.md`: Public-facing overview and quickstart.
- `result.csv`: Preserved experiment data (not used by tutorials).

## Key files and their purposes

- `01-Intro/01-intro.py`: Reference pattern—load env vars, configure Ollama model, define Tavily tool, build deep agent, run a research task, and log the trace/summary.
- `01-Intro/01-intro copy.py`: Quick smoke-test script for a tiny local model.
- `utils.py`: `print_agent_execution`, `print_agent_summary`, `save_agent_result` for observability and persistence.

## Build and run commands

- Create env + install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run main tutorial: `python 01-Intro/01-intro.py`
- Run minimal variant: `python "01-Intro/01-intro copy.py"`

## Code style guidelines

- Prefer type hints and small, focused functions.
- Keep secrets in `.env`; do not hardcode keys.
- Favor Ollama-backed models by default; gate hosted models behind env vars.
- Add concise comments only where logic is non-obvious (avoid noise).
- Keep examples runnable end-to-end (no missing env/config assumptions).

## Testing instructions

- No formal test suite yet. For now, run the tutorial scripts end-to-end to validate changes and ensure agent traces print without errors.
