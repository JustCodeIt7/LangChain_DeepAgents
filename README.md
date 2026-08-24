# LangChain Deep Agents Tutorials

A YouTube tutorial series on building AI agents with LangChain's [`deepagents`](https://github.com/langchain-ai/deepagents) package. The examples are local-first (Ollama) and cloud-ready (OpenAI), and each one is a self-contained script you can run end-to-end.

The repo contains three tutorial series, plus a legacy research track:

| Series | Episodes | What it builds | deepagents |
|---|---|---|---|
| [**Deep Agents 101**](deepagents_101/) | 20 | The framework fundamentals — one concept per episode | 0.7.x |
| [**CodeIt**](episodes/) | 15 | A full coding agent from scratch: model factory → tools → permissions → sub-agents → MCP → a real CLI | 0.6.x |
| [**DeepCoder**](deepcoding_agent/) | 14 | A terminal coding agent with a Textual TUI: chat loop → streaming → approvals → sessions → sub-agents | 0.7.x |
| Legacy research agents | — | Research agents with web search (Tavily) and a Streamlit UI | 0.6.x |

New to `deepagents`? Start with [Deep Agents 101](deepagents_101/).

## Deep Agents 101: the fundamentals

Each episode in [`deepagents_101/`](deepagents_101/) is one self-contained script (under 150 lines, with `# %%` cell markers so you can run it cell-by-cell in VS Code). Nothing is shared between episodes — jump straight to the topic you care about.

| # | Episode | What you learn |
|---|---------|----------------|
| 01 | [deepagent_intro](deepagents_101/01-deepagent_intro/) | `create_deep_agent()`, and the tools every agent gets for free |
| 02 | [models_and_prompts](deepagents_101/02-models_and_prompts/) | Model strings vs. instances, `system_prompt`, `debug=True` |
| 03 | [custom_tools](deepagents_101/03-custom_tools/) | Plain functions and `@tool`; custom tools are additive |
| 04 | [planning_todos](deepagents_101/04-planning_todos/) | `TodoListMiddleware` and `write_todos` (opt-in in 0.7) |
| 05 | [virtual_filesystem](deepagents_101/05-virtual_filesystem/) | `StateBackend`: seed files in, read them back out |
| 06 | [real_filesystem](deepagents_101/06-real_filesystem/) | `FilesystemBackend`: editing real files safely |
| 07 | [shell_execute](deepagents_101/07-shell_execute/) | `LocalShellBackend` and the `execute` tool |
| 08 | [composite_backend](deepagents_101/08-composite_backend/) | `CompositeBackend`: route paths to different backends |
| 09 | [subagents_basics](deepagents_101/09-subagents_basics/) | The `task` tool and context isolation |
| 10 | [custom_subagents](deepagents_101/10-custom_subagents/) | Per-subagent tools/models; `CompiledSubAgent` |
| 11 | [structured_output](deepagents_101/11-structured_output/) | `response_format` and `structured_response` |
| 12 | [checkpointer_threads](deepagents_101/12-checkpointer_threads/) | Checkpointers, `thread_id`, multi-turn memory |
| 13 | [human_in_the_loop](deepagents_101/13-human_in_the_loop/) | `interrupt_on`, approve/reject/edit/respond |
| 14 | [permissions](deepagents_101/14-permissions/) | `FilesystemPermission`: allow, deny, interrupt |
| 15 | [long_term_memory](deepagents_101/15-long_term_memory/) | `StoreBackend` + `memory=` across conversations |
| 16 | [skills](deepagents_101/16-skills/) | `SKILL.md` packages and progressive disclosure |
| 17 | [streaming](deepagents_101/17-streaming/) | `stream_mode="updates"` vs `"messages"` |
| 18 | [context_management](deepagents_101/18-context_management/) | Automatic summarization of long conversations |
| 19 | [capstone_research](deepagents_101/19-capstone_research/) | Everything combined: a research agent |
| 20 | [mcp_tools](deepagents_101/20-mcp_tools/) | MCP tools via `MultiServerMCPClient` (async) |

Each episode folder contains the script and a `README.md` with the goal, key concepts, run instructions, and env vars. Episodes 06–08 write to a per-episode `workspace/` folder (git-ignored).

## CodeIt: building a coding agent

Each episode in [`episodes/`](episodes/) is a standalone, heavily-commented Python script that builds on the previous one. Run them in order to follow the full build.

| # | Episode | What you build |
|---|---------|----------------|
| 1 | [model-factory](episodes/01-model-factory/) | Provider-agnostic model factory (Ollama/OpenAI) + a minimal agent |
| 2 | [agentic-loop](episodes/02-agentic-loop/) | A custom `@tool` + live streaming of the reasoning loop |
| 3 | [filesystem-tools](episodes/03-filesystem-tools/) | `FilesystemBackend` for safe code exploration |
| 4 | [write-sandbox](episodes/04-write-sandbox/) | `write_file` + the workspace sandbox |
| 5 | [shell-tool](episodes/05-shell-tool/) | A custom shell tool (and why it's dangerous) |
| 6 | [approval-gate](episodes/06-approval-gate/) | Human-in-the-loop permission gating |
| 7 | [system-prompt](episodes/07-system-prompt/) | Engineering personality & rules via the system prompt |
| 8 | [surgical-edits](episodes/08-surgical-edits/) | `edit_file` + a fuzzy fallback wrapper |
| 9 | [repo-map](episodes/09-repo-map/) | Context management: repo map & token trimming |
| 10 | [todo-planning](episodes/10-todo-planning/) | TodoList & task decomposition |
| 11 | [error-recovery](episodes/11-error-recovery/) | Self-healing error-recovery loops |
| 12 | [subagents](episodes/12-subagents/) | Sub-agents: specialists in isolated context |
| 13 | [mcp-skills](episodes/13-mcp-skills/) | MCP + Skills: the standard protocol |
| 14 | [cli-streaming](episodes/14-cli-streaming/) | Shipping CodeIt: a real CLI with event streaming |
| 15 | [stretch](episodes/15-stretch/) | LangSmith observability appendix |

Each episode folder contains the script (`NN-name.py`) and a `README.md` with the goal, key concepts, run instructions, and env vars.

## DeepCoder: a terminal coding agent

Each episode in [`deepcoding_agent/`](deepcoding_agent/) is a small multi-module app that builds on the previous one: `main.py` (entry), `config.py` (all env vars in one place), `agent.py` (model + backend + agent), `runner.py` (the event stream), `tui.py` (the Textual UI), plus `commands.py` / `widgets.py` / `sessions.py` as they are introduced, and a `test_smoke.py` that drives the UI with fake agents (no model needed).

| # | Episode | What you build |
|---|---------|----------------|
| 01 | [intro](deepcoding_agent/01-intro/) | Your first coding agent: `create_deep_agent()` + one question |
| 02 | [chat-loop](deepcoding_agent/02-chat-loop/) | A multi-turn chat loop |
| 03 | [project-files](deepcoding_agent/03-project-files/) | Point the agent at real project files |
| 04 | [shell-execute](deepcoding_agent/04-shell-execute/) | Shell execution via the `execute` tool |
| 05 | [approvals](deepcoding_agent/05-approvals/) | An approval gate for dangerous tools |
| 06 | [streaming](deepcoding_agent/06-streaming/) | Stream the agent's events as they happen |
| 07 | [streaming-approvals](deepcoding_agent/07-streaming-approvals/) | Streaming + approvals combined |
| 08 | [textual-shell](deepcoding_agent/08-textual-shell/) | The Textual TUI shell |
| 09 | [textual-worker](deepcoding_agent/09-textual-worker/) | The agent on a worker thread |
| 10 | [approval-modal](deepcoding_agent/10-approval-modal/) | An approval modal in the TUI |
| 11 | [plan-status](deepcoding_agent/11-plan-status/) | A plan panel showing the agent's todos |
| 12 | [slash-commands](deepcoding_agent/12-slash-commands/) | Slash commands (`/help`, `/new`, `/resume`) |
| 13 | [sessions](deepcoding_agent/13-sessions/) | Sessions that survive a restart (SqliteSaver + thread index) |
| 14 | [subagents](deepcoding_agent/14-subagents/) | Sub-agents with nested rendering |

## Setup

**Prerequisites**

- Python 3.11+
- [Ollama](https://ollama.ai) for local models — or an OpenAI API key
- A [Tavily](https://tavily.com) API key (legacy research track only)

**Install dependencies**

The project is managed with [uv](https://docs.astral.sh/uv/) (see `pyproject.toml` + `uv.lock`):

```bash
uv sync            # creates .venv and installs all deps
source .venv/bin/activate
```

> **Note on deepagents versions.** `pyproject.toml` pins `deepagents==0.6.12`, which matches the CodeIt series. **Deep Agents 101 and DeepCoder are written against deepagents 0.7.x** — for those series, upgrade in your env: `pip install -U "deepagents>=0.7"`. (The 101 series README also documents a plain conda + pip setup: `conda activate py313 && pip install -U deepagents langchain-mcp-adapters python-dotenv rich`.)

Or with plain pip:

```bash
python -m venv .venv && source .venv/bin/activate
pip install deepagents langchain langchain-ollama langchain-openai rich python-dotenv
```

**Configure environment**

```bash
cp .env.example .env
# edit .env — set LLM_PROVIDER, LLM_MODEL, and any API keys
```

**Pull a model**

```bash
ollama pull qwen3.5:9b        # Deep Agents 101 + DeepCoder default
ollama pull qwen2.5-coder:7b  # CodeIt default (LLM_MODEL)
ollama pull gpt-oss:20b       # legacy research track
```

## Running an episode

**Deep Agents 101** — one env var controls the model (any LangChain provider string):

```bash
cd deepagents_101/01-deepagent_intro
python 01-deepagent_intro.py
DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 01-deepagent_intro.py
```

**CodeIt** — pass a prompt as the first argument:

```bash
cd episodes/01-model-factory
LLM_PROVIDER=ollama python 01-model-factory.py "Say hello in one sentence."

# Cloud OpenAI
LLM_PROVIDER=openai OPENAI_API_KEY=your-key LLM_MODEL=gpt-4o-mini \
    python 01-model-factory.py "Hello"

# Later episodes that touch the filesystem take a working directory:
CODEIT_WORKDIR=./workspace python 05-shell-tool.py "List the files in the workspace."
```

**DeepCoder** — a Textual TUI (ctrl+c to quit):

```bash
cd deepcoding_agent/14-subagents
python main.py

# Point it at a real project and skip approval prompts (demos only):
DEEPCODER_WORKDIR=/path/to/project DEEPCODER_AUTO_APPROVE=1 python main.py
```

## Environment variables

**Deep Agents 101**

| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string (`openai:gpt-4.1-mini`, …) |

**CodeIt** (documented in `.env.example`)

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Provider selector: `ollama` or `openai` |
| `LLM_MODEL` | `qwen2.5-coder:7b` | Model name (e.g. `gpt-4o-mini` for OpenAI) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `OPENAI_API_KEY` | *(empty)* | Required when `LLM_PROVIDER=openai` |
| `OPENAI_BASE_URL` | *(empty)* | Optional override for OpenAI-compatible endpoints |
| `CODEIT_WORKDIR` | `./workspace` | Working directory the agent's file/shell tools operate in |
| `CODEIT_AUTO_APPROVE` | `false` | Skip the approval gate (the `--yolo` flag sets this at runtime) |
| `CODEIT_MAX_ITERS` | `25` | Recursion-limit guard for the agent loop |

**DeepCoder**

| Variable | Default | Description |
|---|---|---|
| `DEEPCODER_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |
| `DEEPCODER_WORKDIR` | `./workspace` | Directory the agent is allowed to read and write |
| `DEEPCODER_KEEP_ALIVE` | `30m` | How long Ollama keeps the model loaded between turns |
| `DEEPCODER_NUM_CTX` | `8192` | Context window (Ollama's small default truncates silently) |
| `DEEPCODER_SHELL_TIMEOUT` | `120` | Max seconds a single shell command may run |
| `DEEPCODER_AUTO_APPROVE` | *(empty)* | `1` skips every approval prompt — handy for demos, a bad idea near a repo you care about |

Provider keys (`OPENAI_API_KEY`, …) go in the repo-root `.env` — every script calls `load_dotenv()`.

## Project structure

```
.
├── deepagents_101/            # 101 series — 20 self-contained episodes (deepagents 0.7.x)
│   ├── 01-deepagent_intro/    #   each: NN-name.py + README.md
│   ├── ...
│   └── 20-mcp_tools/
├── episodes/                  # CodeIt series — 15 standalone episodes
│   ├── 01-model-factory/      #   each: NN-name.py + README.md
│   ├── ...
│   └── 15-stretch/
├── deepcoding_agent/          # DeepCoder series — 14 multi-module Textual TUI episodes
│   ├── 01-intro/              #   each: main.py + config.py + agent.py + ... + test_smoke.py
│   ├── ...
│   └── 14-subagents/
├── 01-Intro/                  # Legacy: research agent with Tavily web search
├── DeepResearch/              # Legacy: Streamlit + LangGraph research assistant
├── utils.py                   # Legacy: trace/summary/save helpers
├── pyproject.toml             # codeit package config (uv-managed)
├── uv.lock
├── .env.example               # env var template
└── README.md
```

## Testing & lint

```bash
ruff check .                          # lint (config in pyproject.toml)
pytest deepcoding_agent/              # DeepCoder smoke tests — fake agents, no model needed
```

The DeepCoder smoke tests drive the Textual app with fake agents, so they run offline. `episodes/` and `deepagents_101/` have no test suite — validate changes by running the affected script end-to-end.

## Legacy: research agents

Before the three series above, the repo contained two research-focused examples:

- **`01-Intro/01-intro.py`** — a deep research agent that uses Tavily web search, planning, and trace logging.
- **`DeepResearch/`** — a Streamlit web UI over a LangGraph plan → search → synthesize workflow (own `requirements.txt` + `.env.example`; run with `streamlit run app.py`).

See [`01-Intro/`](01-Intro/) and [`DeepResearch/README.md`](DeepResearch/README.md) for details.

## License

MIT — see [LICENSE](LICENSE).
