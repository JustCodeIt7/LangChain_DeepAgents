# LangChain Deep Agents Tutorials

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![deepagents 0.7.x](https://img.shields.io/badge/deepagents-0.7.x-1C3C3C)](https://github.com/langchain-ai/deepagents)
[![Local-First: Ollama](https://img.shields.io/badge/local--first-Ollama-000000)](https://ollama.com)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Hands-on YouTube tutorials, notebooks, runnable app snapshots, and study notes for building AI agents with LangChain's [`deepagents`](https://github.com/langchain-ai/deepagents) package — an agent harness built on LangChain and LangGraph that gives a model a filesystem, planning, subagents, and human-in-the-loop oversight out of the box.

Every example is **local-first** ([Ollama](https://ollama.com)) and **cloud-ready** (OpenRouter, OpenAI, or any LangChain provider), designed to run end-to-end with zero hidden boilerplate.

[Tracks](#tracks) · [Quick Start](#quick-start) · [Deep Agents 101](#deep-agents-101) · [DeepCoder](#deepcoder) · [Study Notes and Tools](#study-notes-and-tools) · [Configuration](#configuration) · [Repository Layout](#repository-layout) · [Testing and Lint](#testing-and-lint) · [Legacy Research Agents](#legacy-research-agents)

---

## Tracks

| Track | Location | Format | What you get | `deepagents` |
| --- | --- | --- | --- | --- |
| [**Deep Agents 101**](deepagents_101/) | `deepagents_101/` | 21 standalone episodes (`.py` + `.ipynb` + slides + diagrams) | Framework fundamentals — one focused concept per episode | `0.7.x` |
| [**DeepCoder**](deepcoding_agent/) | `deepcoding_agent/` | 18 progressive app snapshots + Textual TUI + smoke tests | Build a local Claude Code / opencode-style terminal coding agent from scratch | `0.7.x` |
| [**Agentic Design Patterns**](Agentic_Design_Patterns-Notes.md) | Root Markdown & PDF | Study notes + 21-episode series blueprint | Architecture reference covering 21 core agentic patterns with Mermaid diagrams | — |
| [**Legacy Research Agents**](#legacy-research-agents) | `01-Intro/`, `DeepResearch/` | Standalone script & Streamlit app | Early web-search research agents powered by Tavily and LangGraph | `0.6.x` |

> [!TIP]
> **Where to start?** New to `deepagents`? Start with [**Deep Agents 101**](deepagents_101/) to learn the API one building block at a time. Want to assemble a real interactive coding agent with streaming, diffs, approvals, SQLite sessions, subagents, and MCP? Jump into [**DeepCoder**](deepcoding_agent/).

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com)** running locally (`ollama serve`) — or a cloud provider key (OpenRouter / OpenAI)
- A **[Tavily](https://tavily.com)** API key *(legacy research track only)*

### 1. Create an environment and install dependencies

Choose the dependency set for the track you want to run:

```bash
python -m venv .venv && source .venv/bin/activate
```

**For Deep Agents 101 (`deepagents 0.7.x`):**

```bash
pip install -U "deepagents>=0.7" langchain-ollama langchain-openrouter python-dotenv rich
pip install langchain-mcp-adapters mcp   # only needed for episode 20 (MCP)
```

**For DeepCoder (`deepagents 0.7.x` + Textual TUI):**

Part 18 includes a complete [`pyproject.toml`](deepcoding_agent/18-mcp-packaging/pyproject.toml) that installs every dependency (plus the `deepcoder` CLI command):

```bash
cd deepcoding_agent/18-mcp-packaging
pip install -e ".[mcp,dev]"   # omit [mcp,dev] if you don't need MCP or pytest/ruff
```

> [!NOTE]
> **About the repo-root `pyproject.toml`:** The root [`pyproject.toml`](pyproject.toml) still pins `deepagents==0.6.12` from an earlier archived track. Both active series (**Deep Agents 101** and **DeepCoder**) target **`deepagents 0.7.x`** (`deepagents.backends`, `TodoListMiddleware`, `FilesystemPermission`, opt-in `write_todos`). Use the `0.7.x` install commands above rather than bare `uv sync` at the repo root.

### 2. Pull a local model & configure `.env`

```bash
ollama serve                  # start Ollama if it isn't already running
ollama pull qwen3.5:2b        # Deep Agents 101 default (fast, lightweight)
ollama pull qwen3.5:9b        # DeepCoder default (better tool-calling reliability)
```

Copy the template if you want to set provider keys, model overrides, or optional LangSmith tracing in one place (every script calls `load_dotenv()`):

```bash
cp .env.example .env
```

### 3. Run your first agent

```bash
# Deep Agents 101 — run a script (or open the matching .ipynb notebook)
cd deepagents_101/01-deepagent_intro
python 01-deepagent_intro.py

# DeepCoder — launch the finished Textual TUI (ctrl+c to quit)
cd deepcoding_agent/18-mcp-packaging
python main.py
# Or, if installed via `pip install -e .`:
deepcoder
```

---

## Deep Agents 101

[`deepagents_101/`](deepagents_101/) teaches the `deepagents 0.7.x` framework one concept at a time. Nothing is shared between episodes, so you can jump straight to any topic.

Every episode folder includes:

- A self-contained **Python script** (`.py`, with `# %%` cell markers for VS Code's Interactive Window)
- A matching **Jupyter notebook** (`.ipynb`)
- A **README**, **3-slide Marp deck** (`slides.md` / `slides.html`), and **Mermaid diagrams** (`diagrams/*.mmd`, `.svg`, `.png`) *(included on episodes `01`–`02` and `03.2`–`20`)*

| # | Episode | What you learn |
| --- | --- | --- |
| 01 | [01-deepagent_intro](deepagents_101/01-deepagent_intro/) | `create_deep_agent()`, state shape, and the tools every agent gets for free |
| 02 | [02-models_and_prompts](deepagents_101/02-models_and_prompts/) | Model strings vs. instances, `system_prompt`, `debug=True` |
| 03.1 | [03.1-builtin_tools](deepagents_101/03.1-builtin_tools/) | Exercising built-in filesystem, `LocalShellBackend` (`execute`), `task`, and `write_todos` tools in a disposable workspace |
| 03.2 | [03.2-custom_tools](deepagents_101/03.2-custom_tools/) | Plain functions & `@tool`, additive tools, structured `dict` returns, `async` tools, and `return_direct` |
| 04.2 | [04.2-planning_todos](deepagents_101/04.2-planning_todos/) | `TodoListMiddleware` and `write_todos` (opt-in in `deepagents 0.7`) |
| 05 | [05-virtual_filesystem](deepagents_101/05-virtual_filesystem/) | `StateBackend`: seed virtual files in, read agent-created files back out |
| 06 | [06-real_filesystem](deepagents_101/06-real_filesystem/) | `FilesystemBackend`: reading and editing real disk files safely |
| 07 | [07-shell_execute](deepagents_101/07-shell_execute/) | `LocalShellBackend` and the `execute` tool |
| 08 | [08-composite_backend](deepagents_101/08-composite_backend/) | `CompositeBackend`: route path prefixes to different backends |
| 09 | [09-subagents_basics](deepagents_101/09-subagents_basics/) | The `task` tool and context isolation |
| 10 | [10-custom_subagents](deepagents_101/10-custom_subagents/) | Per-subagent tools/models and `CompiledSubAgent` |
| 11 | [11-structured_output](deepagents_101/11-structured_output/) | `response_format` and `structured_response` with Pydantic |
| 12 | [12-checkpointer_threads](deepagents_101/12-checkpointer_threads/) | Checkpointers, `thread_id`, and multi-turn conversation memory |
| 13 | [13-human_in_the_loop](deepagents_101/13-human_in_the_loop/) | `interrupt_on`, `Command(resume=...)`, approve / reject / edit / respond |
| 14 | [14-permissions](deepagents_101/14-permissions/) | `FilesystemPermission`: allow, deny, and interrupt rules |
| 15 | [15-long_term_memory](deepagents_101/15-long_term_memory/) | `StoreBackend` + `memory=` across separate conversations |
| 16 | [16-skills](deepagents_101/16-skills/) | `SKILL.md` packages and progressive disclosure |
| 17 | [17-streaming](deepagents_101/17-streaming/) | `stream_mode="updates"` vs. `stream_mode="messages"` |
| 18 | [18-context_management](deepagents_101/18-context_management/) | `SummarizationMiddleware` for automatic compression of long histories |
| 19 | [19-capstone_research](deepagents_101/19-capstone_research/) | Everything combined: local-corpus research agent with planning, subagents, and streaming |
| 20 | [20-mcp_tools](deepagents_101/20-mcp_tools/) | Async MCP tools via `MultiServerMCPClient` and a bundled local stdio server |

**Switching models in Deep Agents 101:** Scripts default to local Ollama via `OLLAMA_MODEL` (default `qwen3.5:2b`) and `OLLAMA_BASE_URL` (default `http://localhost:11434`). Each script also includes a commented `ChatOpenRouter` block if you prefer a hosted model. Smaller local models occasionally skip multi-tool steps — override with a larger model (`OLLAMA_MODEL=qwen3.5:9b python ...`) if an agent misses a tool call.

See [`deepagents_101/README.md`](deepagents_101/README.md) for series notes.

---

## DeepCoder

[`deepcoding_agent/`](deepcoding_agent/) builds a complete, local-first terminal coding agent (in the spirit of Claude Code and opencode) in **18 incremental parts** using `deepagents 0.7.x`, Ollama, and [Textual](https://textual.textualize.io).

- **≤150 lines of new code per part** — enforced across all 18 parts by [`deepcoding_agent/_tools/diff_lines.py`](deepcoding_agent/_tools/diff_lines.py).
- **Every part is a complete, runnable snapshot** — `cd` into any part folder and run `python main.py`.
- **Offline headless tests** — Parts 08–18 each ship a `test_smoke.py` that drives the real Textual app through `Pilot` with stub agents (no model or Ollama required).

| # | Part | What you build | New deps |
| --- | --- | --- | --- |
| 01 | [01-intro](deepcoding_agent/01-intro/) | First coding agent: `create_deep_agent`, model strings, built-in toolbox | — |
| 02 | [02-chat-loop](deepcoding_agent/02-chat-loop/) | Multi-turn chat loop with checkpointers and `thread_id` | — |
| 03 | [03-project-files](deepcoding_agent/03-project-files/) | `CompositeBackend`, real project files, and the Ollama `num_ctx` trap | — |
| 04 | [04-shell-execute](deepcoding_agent/04-shell-execute/) | Shell execution via `LocalShellBackend`, `execute`, and `inherit_env` | — |
| 05 | [05-approvals](deepcoding_agent/05-approvals/) | `interrupt_on` approval gate and batched `decisions` list | — |
| 06 | [06-streaming](deepcoding_agent/06-streaming/) | UI-agnostic `runner.py` event layer with dual `stream_mode` | — |
| 07 | [07-streaming-approvals](deepcoding_agent/07-streaming-approvals/) | Pauses as typed events and resuming mid-stream | — |
| 08 | [08-textual-shell](deepcoding_agent/08-textual-shell/) | First Textual TUI shell (intentionally demonstrating UI blocking) | `textual` |
| 09 | [09-textual-worker](deepcoding_agent/09-textual-worker/) | Background thread workers, `post_message`, buffered Markdown updates | — |
| 10 | [10-approval-modal](deepcoding_agent/10-approval-modal/) | Interactive `ModalScreen`, `call_from_thread`, batched approvals | — |
| 11 | [11-plan-status](deepcoding_agent/11-plan-status/) | `TodoListMiddleware`, live plan sidebar, and token counts | — |
| 12 | [12-slash-commands](deepcoding_agent/12-slash-commands/) | Slash command registry (`/help`, `/new`, `/clear`, `/model`, `/quit`) with autocomplete | — |
| 13 | [13-sessions](deepcoding_agent/13-sessions/) | Persistent SQLite sessions (`SqliteSaver`) + `/resume` picker | `langgraph-checkpoint-sqlite` |
| 14 | [14-subagents](deepcoding_agent/14-subagents/) | Subagent delegation, context quarantine, and `subgraphs=True` rendering | — |
| 15 | [15-project-memory](deepcoding_agent/15-project-memory/) | Project memory (`AGENTS.md` via `memory=`) and `/init` command | — |
| 16 | [16-diffs](deepcoding_agent/16-diffs/) | Syntax-highlighted unified diffs inside the approval modal | — |
| 17 | [17-health-polish](deepcoding_agent/17-health-polish/) | Actionable startup health checks (`health.py`) and keybindings | — |
| 18 | [18-mcp-packaging](deepcoding_agent/18-mcp-packaging/) | Optional MCP servers (`mcp.json`), async-to-sync bridge, `deepcoder` CLI packaging | `langchain-mcp-adapters` |

### Final Architecture (Part 18)

```text
18-mcp-packaging/
├── main.py                # Entry point: load optional MCP tools, start Textual
├── tui.py                 # Textual App: layout, worker thread, message handlers
├── runner.py              # UI-agnostic event stream wrapper over agent.stream()
├── agent.py               # Model, CompositeBackend, subagents, approval gates, memory
├── config.py              # All DEEPCODER_* settings read once from environment
├── widgets.py             # Approval modal (with diffs), resume picker, plan sidebar
├── commands.py            # /help /new /clear /model /init /resume /quit
├── sessions.py            # SQLite checkpointer, thread index, and history replay
├── health.py              # Startup environment & Ollama checks
├── mcp_tools.py           # Optional mcp.json loader + sync bridge for async MCP tools
├── example_mcp_server.py  # Minimal local MCP demo server (pair with mcp.json.example)
├── app.tcss               # Textual CSS styling
├── pyproject.toml         # Dependencies + `deepcoder` console script entry point
└── test_smoke.py          # Headless Pilot UI tests with stub agents
```

**Running DeepCoder against a real project:**

```bash
cd deepcoding_agent/18-mcp-packaging

# Optional: enable the bundled demo MCP server
cp mcp.json.example mcp.json

# Point DeepCoder at any project folder (omit DEEPCODER_AUTO_APPROVE for normal safety!)
DEEPCODER_WORKDIR=/path/to/your/project python main.py

# Or switch to any LangChain cloud model
DEEPCODER_MODEL=openai:gpt-4.1-mini DEEPCODER_WORKDIR=/path/to/your/project python main.py
```

See [`deepcoding_agent/README.md`](deepcoding_agent/README.md) for the full series walkthrough — including the three real-world traps encountered during the build (batched approval `decisions`, `Markdown.update()` races, and bridging async-only MCP tools).

---

## Study Notes and Tools

### Agentic Design Patterns Study Notes

Comprehensive study notes and a 21-episode YouTube curriculum blueprint synthesizing Antonio Gulli's *Agentic Design Patterns: A Hands-On Guide to Building Intelligent Systems*:

- [`Agentic_Design_Patterns-Notes.md`](Agentic_Design_Patterns-Notes.md) — full Markdown notes covering all 21 patterns in chapter order, complete with Mermaid architecture diagrams, trade-offs, variations, and demo ideas.
- [`Agentic_Design_Patterns-Notes.pdf`](Agentic_Design_Patterns-Notes.pdf) — formatted PDF edition of the notes.
- [`Agentic Design Patterns - Study Notes.md`](Agentic%20Design%20Patterns%20-%20Study%20Notes.md) — companion synthesis with PDF page references and video timestamps.

### LLM Inference Benchmark (`benchmark_llm.py`)

[`benchmark_llm.py`](benchmark_llm.py) is a standalone CLI (only dependency: `requests`) for benchmarking any OpenAI-compatible inference server (Ollama, LM Studio, vLLM, `llama.cpp` server). It measures sequential TTFT, latency, and tokens/sec, plus concurrent throughput scaling to simulate parallel subagent workloads:

```bash
# Benchmark a local Ollama server
python benchmark_llm.py --base-url http://localhost:11434/v1 --model qwen3.5:9b

# Simulate subagent concurrency (8 parallel requests, 32 total)
python benchmark_llm.py --base-url http://localhost:11434/v1 --model qwen3.5:9b \
    --concurrency 8 --concurrent-requests 32

# Sweep concurrency levels and export JSON metrics
python benchmark_llm.py --base-url http://localhost:11434/v1 --model qwen3.5:9b \
    --sweep 1,2,4,8 --json results.json
```

---

## Configuration

Every script calls `load_dotenv()`, so you can place API keys and overrides in a repo-root `.env` file (git-ignored).

### Deep Agents 101

| Variable | Default | Description |
| --- | --- | --- |
| `OLLAMA_MODEL` | `qwen3.5:2b` | Local Ollama model name used by `ChatOllama` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `OPENROUTER_API_KEY` | *(empty)* | Required only if uncommenting the `ChatOpenRouter` option in a script |

### DeepCoder

| Variable | Default | Description |
| --- | --- | --- |
| `DEEPCODER_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string (e.g., `openai:gpt-4.1-mini`) |
| `DEEPCODER_WORKDIR` | `./workspace` | Directory the agent is allowed to read, edit, and run commands in |
| `DEEPCODER_KEEP_ALIVE` | `30m` | How long Ollama keeps the model loaded between turns |
| `DEEPCODER_NUM_CTX` | `8192` | Context window size (Ollama's smaller default truncates silently) |
| `DEEPCODER_SHELL_TIMEOUT` | `120` | Max seconds a single `execute` command may run |
| `DEEPCODER_AUTO_APPROVE` | *(empty)* | Set to `1` / `true` to skip approval modals (demos only) |

### Optional Cloud & Observability Keys

| Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | Required when using OpenAI models (`openai:...`) |
| `TAVILY_API_KEY` | Required for the legacy web-search research agents (`01-Intro/`, `DeepResearch/`) |
| `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT` | Optional LangSmith trace logging (template in [`.env.example`](.env.example)) |

---

## Repository Layout

```text
.
├── deepagents_101/                           # Deep Agents 101 — 21 episodes (deepagents 0.7.x)
│   ├── 01-deepagent_intro/                   #   .py + .ipynb + README.md + slides + diagrams/
│   ├── ...
│   ├── 20-mcp_tools/
│   └── README.md
├── deepcoding_agent/                         # DeepCoder — 18-part Textual TUI coding agent (0.7.x)
│   ├── 01-intro/                             #   complete runnable snapshot per part
│   ├── ...
│   ├── 18-mcp-packaging/                     #   final app + MCP bridge + pyproject.toml
│   ├── _tools/diff_lines.py                  #   150-line-per-part budget checker
│   └── README.md
├── 01-Intro/                                 # Legacy: standalone Tavily research agent
├── DeepResearch/                             # Legacy: Streamlit + LangGraph research assistant
├── benchmark_llm.py                          # OpenAI-compatible sequential & concurrent LLM benchmark
├── utils.py                                  # Legacy trace, summary, and JSON export helpers
├── Agentic_Design_Patterns-Notes.md          # 21 Agentic Design Patterns study notes (+ Mermaid)
├── Agentic_Design_Patterns-Notes.pdf         # PDF edition of the study notes
├── Agentic Design Patterns - Study Notes.md  # Companion synthesis notes with book/video citations
├── .env.example                              # Environment variable template
├── pyproject.toml                            # Ruff/pytest config & legacy package manifest
├── LICENSE                                   # Apache License 2.0
└── README.md
```

---

## Testing and Lint

```bash
# Lint the repository (configured in pyproject.toml: line-length=100, py311)
ruff check .

# Run one DeepCoder part's headless smoke tests (run inside the part folder)
cd deepcoding_agent/18-mcp-packaging
python -m pytest test_smoke.py -q -p anyio

# Run all DeepCoder headless smoke tests (Parts 08–18, offline, no Ollama needed)
for f in deepcoding_agent/*/test_smoke.py; do
    (cd "$(dirname "$f")" && python -m pytest test_smoke.py -q -p anyio)
done

# Verify DeepCoder's ≤150-line-per-part budget across all 18 parts
python deepcoding_agent/_tools/diff_lines.py
```

`deepagents_101/` episodes are standalone teaching scripts and notebooks without a unit test suite — validate changes by executing the affected script or notebook end-to-end.

---

## Legacy Research Agents

Before the two `deepagents 0.7.x` series above, this repository started with two Tavily-powered research examples:

- **[`01-Intro/01-intro.py`](01-Intro/01-intro.py)** — a single-script deep research agent using Tavily web search, Ollama (`gpt-oss:20b`), and trace/summary utilities from [`utils.py`](utils.py).
- **[`DeepResearch/`](DeepResearch/)** — a Streamlit web UI over a LangGraph `Planning → Research → Synthesis` workflow, complete with its own [`requirements.txt`](DeepResearch/requirements.txt), [`.env.example`](DeepResearch/.env.example), and [`README.md`](DeepResearch/README.md) (`streamlit run app.py`).

---

## License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE) for details.
