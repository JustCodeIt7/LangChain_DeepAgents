# LangChain Deep Agents Tutorials

A YouTube tutorial series on building AI agents with LangChain's [`deepagents`](https://github.com/langchain-ai/deepagents) package. The examples are local-first (Ollama) and cloud-ready (OpenAI), and each one is a self-contained script you can run end-to-end.

The series has two tracks:

- **CodeIt** (main) — build a full coding agent from scratch across 15 episodes: model factory → agentic loop → filesystem & shell tools → permission gating → planning → sub-agents → MCP → a real CLI.
- **Research agents** (legacy) — earlier examples that build research agents with web search (Tavily) and a Streamlit UI.

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

## Setup

**Prerequisites**

- Python 3.11+
- [Ollama](https://ollama.ai) for local models — or an OpenAI API key
- A [Tavily](https://tavily.com) API key (research track only)

**Install dependencies**

The project is managed with [uv](https://docs.astral.sh/uv/) (see `pyproject.toml` + `uv.lock`):

```bash
uv sync            # creates .venv and installs all deps
source .venv/bin/activate
```

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

## Running an episode

Each episode is a standalone script. `cd` into its folder and pass a prompt as the first argument:

```bash
# Local Ollama (default)
cd episodes/01-model-factory
LLM_PROVIDER=ollama python 01-model-factory.py "Say hello in one sentence."

# Cloud OpenAI
LLM_PROVIDER=openai OPENAI_API_KEY=your-key LLM_MODEL=gpt-4o-mini \
    python 01-model-factory.py "Hello"
```

Later episodes that touch the filesystem take a working directory:

```bash
CODEIT_WORKDIR=./workspace python 05-shell-tool.py "List the files in the workspace."
```

## Environment variables

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

## Project structure

```
.
├── episodes/                  # CodeIt series — 15 standalone episodes
│   ├── 01-model-factory/      #   each: NN-name.py + README.md
│   ├── ...
│   └── 15-stretch/
├── 01-Intro/                  # Legacy: research agent with Tavily web search
├── DeepResearch/              # Legacy: Streamlit + LangGraph research assistant
├── utils.py                   # Legacy: trace/summary/save helpers
├── pyproject.toml             # codeit package config (uv-managed)
├── uv.lock
├── .env.example               # env var template
└── README.md
```

## Legacy: research agents

Before the CodeIt series, the repo contained two research-focused examples:

- **`01-Intro/01-intro.py`** — a deep research agent that uses Tavily web search, planning, and trace logging.
- **`DeepResearch/`** — a Streamlit web UI over a LangGraph plan → search → synthesize workflow.

See [`01-Intro/`](01-Intro/) and [`DeepResearch/README.md`](DeepResearch/README.md) for details.

## License

MIT — see [LICENSE](LICENSE).
