# AGENTS.md

## Project overview

A YouTube tutorial project for building AI agents with LangChain's `deepagents` package. The main series is **CodeIt** — 15 episodes in `episodes/` that incrementally build a coding agent (a "coding harness") from a model factory to a full CLI with streaming, sub-agents, and MCP. Each episode is a standalone, heavily-commented Python script.

An older **research** track also lives in the repo (`01-Intro/`, `DeepResearch/`, `utils.py`) — research agents with Tavily web search and a Streamlit UI. Treat it as legacy; new work goes in `episodes/`.

## Preferences and dependencies

1. Python 3.11 or later (see `pyproject.toml`).
2. Dependencies are managed with [uv](https://docs.astral.sh/uv/) via `pyproject.toml` + `uv.lock`:

    ```bash
    uv sync                      # creates .venv, installs all deps
    source .venv/bin/activate
    # or, for a single episode's minimal deps:
    pip install deepagents langchain-ollama rich python-dotenv
    ```

3. Configuration via `.env` (never commit; copy from `.env.example`):

    ```dotenv
    LLM_PROVIDER=ollama              # ollama | openai
    LLM_MODEL=qwen2.5-coder:7b       # e.g. gpt-4o-mini for openai
    OLLAMA_BASE_URL=http://localhost:11434
    OPENAI_API_KEY=                  # required only when LLM_PROVIDER=openai
    OPENAI_BASE_URL=                 # optional override
    CODEIT_WORKDIR=./workspace
    CODEIT_AUTO_APPROVE=false        # --yolo flag sets true at runtime
    CODEIT_MAX_ITERS=25              # agent recursion_limit guard
    ```

4. Default LLM backend: Ollama (local, free). OpenAI is the cloud alternative, gated behind `LLM_PROVIDER=openai` + `OPENAI_API_KEY`.

5. Keep the code simple and focused on demonstrating the concept of the episode. Each episode must be runnable end-to-end on its own.

6. Always load secrets from `.env` using `python-dotenv` (`load_dotenv()` before any `os.getenv`).

7. Use rich print statements for better console output:

    ```python
    from rich import print
    print("Hello, [bold magenta]World[/bold magenta]!")
    ```

8. Episodes are self-contained: each `NN-name.py` imports directly from `deepagents` / `langchain` / stdlib. Do NOT import from a shared `codeit` package — it does not exist yet (`pyproject.toml`'s `packages = ["codeit"]` is the end-goal packaging).

## Project structure

- `episodes/NN-name/NN-name.py`: The CodeIt series — 15 standalone episodes, each building on the previous.
- `episodes/NN-name/README.md`: Per-episode docs — goal, key concepts, run instructions, env vars.
- `01-Intro/01-intro.py`: Legacy research agent (Tavily web search + planning + trace logging).
- `01-Intro/01-intro copy.py`: Legacy minimal variant (git-ignored via `*copy.*`).
- `DeepResearch/`: Legacy Streamlit + LangGraph research assistant (own `requirements.txt` + `.env.example`).
- `utils.py`: Legacy helpers — `print_agent_execution`, `print_agent_summary`, `save_agent_result`.
- `pyproject.toml`: codeit package config (uv-managed; `packages = ["codeit"]` is the end goal).
- `uv.lock`: uv lock file.
- `.env.example`: env var template.
- `result.csv`, `agent_response.json`: preserved experiment data (not used by tutorials).

## Key files and their purposes

- `episodes/01-model-factory/01-model-factory.py`: Reference pattern — `Settings` dataclass, `get_model()` (provider-agnostic), `build_agent()` (wraps `create_deep_agent`), `main()` CLI.
- `episodes/14-cli-streaming/14-cli-streaming.py`: The most complete episode — a real CLI with event streaming.
- `utils.py`: `print_agent_execution`, `print_agent_summary`, `save_agent_result` for observability and persistence (legacy track).

## Build and run commands

- Create env + install: `uv sync && source .venv/bin/activate`
- Run an episode (from its folder): `cd episodes/01-model-factory && LLM_PROVIDER=ollama python 01-model-factory.py "Say hello."`
- Run with OpenAI: `LLM_PROVIDER=openai OPENAI_API_KEY=your-key LLM_MODEL=gpt-4o-mini python 01-model-factory.py "Hello"`
- Run a filesystem episode: `CODEIT_WORKDIR=./workspace python 05-shell-tool.py "List the files."`
- Lint: `ruff check .` (config in `pyproject.toml`)
- Tests: `pytest` (dev extra; `live` marker for real-provider tests, skipped in CI)

## Code style guidelines

- Prefer type hints and small, focused functions.
- Keep secrets in `.env`; do not hardcode keys.
- Favor Ollama-backed models by default; gate hosted models behind env vars.
- Annotate imports with WHY they're needed (the episodes do this heavily — match the style).
- Add concise comments only where logic is non-obvious (avoid noise).
- Keep examples runnable end-to-end (no missing env/config assumptions).
- Line length 100 (ruff); target Python 3.11.

## Testing instructions

- No formal test suite for the episodes yet. Run the episode scripts end-to-end to validate changes and ensure output prints without errors.
- `pyproject.toml` configures pytest with a `live` marker for tests that hit a real model provider (Ollama/OpenAI); these are skipped in CI.
