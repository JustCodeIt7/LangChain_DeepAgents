# Repository Guidelines

## Project Overview

YouTube tutorial repo for LangChain's [`deepagents`](https://github.com/langchain-ai/deepagents) package — an agent harness that gives a model a filesystem, planning, subagents, and human oversight out of the box. All examples are local-first (Ollama) and cloud-ready (OpenAI), and each is self-contained and runnable end-to-end.

Three active tutorial series, plus a legacy research track:

| Series                                                    | Location                                 | Shape                                      | deepagents |
| --------------------------------------------------------- | ---------------------------------------- | ------------------------------------------ | ---------- |
| **CodeIt** — build a coding agent in 15 episodes          | `episodes/`                              | one `NN-name.py` per episode               | 0.6.x      |
| **Deep Agents 101** — framework fundamentals, 20 episodes | `deepagents_101/`                        | one `NN-name.py` per episode, `# %%` cells | 0.7.x      |
| **DeepCoder** — Textual TUI coding agent, 14 episodes     | `deepcoding_agent/`                      | multi-module app per episode               | 0.7.x      |
| Legacy research agents (Tavily search, Streamlit UI)      | `01-Intro/`, `DeepResearch/`, `utils.py` | standalone scripts                         | 0.6.x      |

## Architecture & Data Flow

Every series converges on one core: `create_deep_agent(model, tools, system_prompt, ...)` compiles a LangGraph agent; `agent.invoke({"messages": [...]})` returns the final state dict (`messages` + `files`). Built-in tools come free: `ls`/`read_file`/`write_file`/`edit_file`/`delete`/`glob`/`grep` (filesystem), `execute` (shell backend), `task` (subagents), `write_todos` (planning).

**Backends** decide where file tools operate: `StateBackend` (in-memory virtual fs), `FilesystemBackend` (real disk), `LocalShellBackend` (adds `execute`), `CompositeBackend` (routes paths to different backends — DeepCoder uses real disk + an in-memory scratch area).

**Approval gating** is the shared human-in-the-loop pattern: dangerous tools (`execute`, `write_file`, `edit_file`, `delete`) are listed in `GATED_TOOLS` / `INTERRUPT_ON`; the agent pauses via a LangGraph interrupt, and the caller resumes with `Command(resume={"decisions": [...]})`. Read-only tools run ungated.

**DeepCoder data flow** (most complete app, `deepcoding_agent/14-subagents/`):
Textual `Input` → worker thread (agent never touches widgets) → `runner.run_turn()` streams LangGraph events as typed dataclasses (`Token`, `ToolStart`, `Plan`, `ApprovalNeeded`, `Done`, `Failed`) → worker posts Textual `Message`s (`Chunk`, `ToolLine`, `PlanUpdate`, `Finished`) → UI updates Markdown widgets. On `ApprovalNeeded` the worker blocks on `call_from_thread` until the approval modal returns a decision for every pending action, then `resume_with(decisions)` continues the turn. Sessions persist via `SqliteSaver` + a `threads.json` index in `.deepcoder/` inside the workdir.

**CodeIt data flow** (`episodes/14-cli-streaming/`): Typer CLI → optional async MCP tool load (graceful degradation: returns `[]` when unconfigured) → `build_agent()` (model + `FilesystemBackend` + custom `run_shell` tool + `INTERRUPT_ON`) → v3 event streaming with v2 fallback, or an approval loop → Rich panels.

## Key Directories

- `episodes/NN-name/` — CodeIt series; each folder has `NN-name.py` + `README.md` (goal, concepts, run instructions, env vars). Episodes build on each other; run in order.
- `deepagents_101/NN-name/` — 101 series; one script per episode, nothing shared between episodes. Episodes 06–08 write to a per-episode `workspace/` (git-ignored).
- `deepcoding_agent/NN-name/` — DeepCoder series; each episode is a small app: `main.py` (entry), `config.py` (all env vars in one place), `agent.py` (model/backend/agent construction), `runner.py` (event stream), `tui.py` (Textual UI), plus `commands.py` (slash commands, ep 12+), `widgets.py` (modals/panels, ep 10+), `sessions.py` (persistence, ep 13+), `test_smoke.py`. `_tools/` holds shared helpers.
- `01-Intro/`, `DeepResearch/`, `utils.py` — legacy research track; treat as reference, not as the pattern to copy.
- `codeit.egg-info/` — stale build artifact. The `codeit/` package does **not** exist yet; `pyproject.toml`'s `packages = ["codeit"]` is the end goal. Do not import from `codeit`.

## Development Commands

```bash
# Setup (uv is the package manager; uv.lock is committed)
uv sync && source .venv/bin/activate

# Ollama must be running for default models
ollama serve
ollama pull qwen3.5:9b        # deepagents_101 + deepcoding_agent default
ollama pull qwen2.5-coder:7b  # CodeIt default (LLM_MODEL)
ollama pull gpt-oss:20b       # legacy track

# Run CodeIt (from its folder; prompt is argv[1])
cd episodes/01-model-factory
LLM_PROVIDER=ollama python 01-model-factory.py "Say hello in one sentence."
LLM_PROVIDER=openai OPENAI_API_KEY=... LLM_MODEL=gpt-4o-mini python 01-model-factory.py "Hello"
CODEIT_WORKDIR=./workspace python 05-shell-tool.py "List the files."

# Run 101 (model override via one env var; any LangChain provider string)
cd deepagents_101/01-deepagent_intro
python 01-deepagent_intro.py
DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 01-deepagent_intro.py

# Run DeepCoder (Textual TUI; ctrl+c to quit)
cd deepcoding_agent/14-subagents
python main.py
DEEPCODER_WORKDIR=/path/to/project DEEPCODER_AUTO_APPROVE=1 python main.py

# Lint
ruff check .

# Tests (see Testing & QA — bare `pytest` finds nothing)
pytest deepcoding_agent/14-subagents/test_smoke.py

# Legacy Streamlit app (own venv + requirements.txt inside DeepResearch/)
cd DeepResearch && streamlit run app.py
```

## Code Conventions & Common Patterns

- **Env vars**: `load_dotenv()` before any `os.getenv`; secrets only in `.env` (never commit; copy from `.env.example`). Each series has its own prefix: `CODEIT_*` (episodes), `DEEPCODER_*` (deepcoding_agent), `DEEPAGENTS_MODEL` (101). `.env.example` documents only the CodeIt vars — the others are defined in each series' `config.py`/scripts.
- **Model configuration**: CodeIt builds a model _instance_ via `init_chat_model` (owns the error messages, e.g. "OPENAI_API_KEY is required"); 101 and DeepCoder pass a provider _string_ (`"ollama:qwen3.5:9b"`) straight to `create_deep_agent`.
- **`text_of()` helper**: Ollama returns `content` as a string; OpenAI returns a list of content blocks. Every series carries a small `text_of(message)` normalizer — copy the pattern, don't re-derive it.
- **Console output**: `from rich import print` for color tags; DeepCoder renders answers through `rich.markdown.Markdown`.
- **Cell markers**: `# %%` comments make 101, DeepCoder, and 01-Intro scripts runnable cell-by-cell in VS Code's interactive window. Match the style when editing those series.
- **Annotated imports**: CodeIt episodes annotate every import with WHY it's needed — match that style in `episodes/`.
- **Tool docstrings are prompts**: they tell the model WHEN to use the tool and WHAT each arg is. Write them for the model, not just for humans.
- **System prompts**: role + available tools + output format, kept under ~10 lines.
- **Ollama tuning**: set `num_ctx` explicitly (Ollama's small default truncates _silently_, making the agent seem to "forget"); raise `keep_alive` for long interactive sessions (DeepCoder uses 8192 / 30m).
- **Graceful degradation**: optional integrations (MCP) return empty results instead of raising when unconfigured.
- **DeepCoder imports are bare** (`import config`, `from tui import DeepCoderApp`) — run from inside the episode folder.
- **Size limits**: 101 episodes stay under 150 lines (per its README); CodeIt episodes grow as features accumulate (up to ~480 lines, heavily commented). New episodes must be self-contained and runnable end-to-end.
- **Style**: type hints, small focused functions, line length 100 (ruff `E,F,I,UP,B`, target py311).

## Important Files

- `episodes/01-model-factory/01-model-factory.py` — CodeIt reference pattern: `Settings` frozen dataclass, `get_settings()`, `get_model()`, `build_agent()`, `main()`.
- `episodes/14-cli-streaming/14-cli-streaming.py` — most complete CodeIt episode (Typer CLI, v3/v2 streaming, approval gate, MCP loader).
- `deepcoding_agent/14-subagents/` — most complete DeepCoder episode; read `config.py` → `agent.py` → `runner.py` → `tui.py` → `sessions.py` in that order.
- `deepagents_101/01-deepagent_intro/01-deepagent_intro.py` — 101 reference; documents the built-in tool suite.
- `utils.py` — legacy helpers: `print_agent_execution`, `print_agent_summary`, `save_agent_result`.
- `pyproject.toml` — dependencies, ruff config, pytest config.
- `.env.example` — env var template (CodeIt vars only).
- `uv.lock` — committed lockfile; keep in sync with `pyproject.toml`.

## Runtime/Tooling Preferences

- **Python ≥ 3.11** (`pyproject.toml`). The 101 README assumes a conda `py313` env; DeepResearch wants 3.12+. For the root project, **uv is authoritative** (`.vscode/settings.json` still prefers conda — stale).
- **⚠️ Version skew**: `pyproject.toml` pins `deepagents==0.6.12`, but `deepagents_101/` and `deepcoding_agent/` are written against **0.7.x** APIs (`deepagents.backends` imports, `TodoListMiddleware`, the `delete` tool, opt-in `write_todos`). `uv sync` installs 0.6.12, which breaks the newer series — bump the pin (and `uv lock`) or run those series in a separate env with deepagents 0.7.x.
- **Ollama** must be running locally for the default models; OpenAI is the cloud alternative, gated behind env vars.
- **MCP**: `opencode.json` and `.mcp.json` both configure the "Docs by LangChain" server (`https://docs.langchain.com/mcp`) for agent tooling.
- **Git-ignored**: `.env`, `.venv`, `*copy.*` (tutorial variants), per-series `workspace/` and `deepcoding_agent/**/.deepcoder/`, and all dotdirs except `.github/`.

## Testing & QA

- **Framework**: pytest + anyio (asyncio backend; anyio ships its own pytest plugin, so no extra test dep).
- **Where tests live**: `deepcoding_agent/NN-name/test_smoke.py` — one per episode. They drive the Textual app with **fake agents** (e.g. `PlanningAgent`, `GatedAgent`) so no model or network is needed. Run one: `pytest deepcoding_agent/14-subagents/test_smoke.py`; run the series: `pytest deepcoding_agent/`.
- **Gotcha**: `pyproject.toml` sets `testpaths = ["tests"]`, but no root `tests/` directory exists — bare `pytest` collects nothing. Always pass a path.
- **`live` marker**: defined in `pyproject.toml` for tests that hit a real model provider (skipped in CI); currently unused by the smoke tests.
- **Coverage**: none configured; smoke tests only. `episodes/` and `deepagents_101/` are untested — validate changes by running the affected script end-to-end and checking the printed output.
