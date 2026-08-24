# Deep Agents 101

A 20-part tutorial series on **`deepagents`** — LangChain's agent harness that gives a model a
filesystem, planning, subagents, and human oversight out of the box.

Each episode is **one self-contained Python script** under 150 lines. Nothing is shared between
episodes, so you can jump straight to the topic you care about.

## Setup

```bash
conda activate py313
pip install -U deepagents langchain-mcp-adapters python-dotenv rich
```

Written against **deepagents 0.7.x**. Episode 20 is the only one needing `langchain-mcp-adapters`.

## Choosing a model

Every script reads one environment variable and falls back to a local Ollama model:

```python
MODEL = os.getenv("DEEPAGENTS_MODEL", "ollama:qwen3.5:2b")
```

Run with the default (requires `ollama serve` and `ollama pull qwen3.5:2b`):

```bash
python 01-deepagent_intro/01-deepagent_intro.py
```

Or point it at any provider LangChain supports:

```bash
DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 01-deepagent_intro/01-deepagent_intro.py
```

Put provider keys in the repo-root `.env` — every script calls `load_dotenv()`.
Smaller local models follow multi-tool instructions less reliably; if an episode's agent skips a
step, try a larger model before assuming the code is wrong.

## Episodes

| #   | Episode                   | What you learn                                                 |
| --- | ------------------------- | -------------------------------------------------------------- |
| 01  | `01-deepagent_intro`      | `create_deep_agent()`, and the tools every agent gets for free |
| 02  | `02-models_and_prompts`   | Model strings vs. instances, `system_prompt`, `debug=True`     |
| 03  | `03-custom_tools`         | Plain functions and `@tool`; custom tools are additive         |
| 04  | `04-planning_todos`       | `TodoListMiddleware` and `write_todos` (opt-in in 0.7)         |
| 05  | `05-virtual_filesystem`   | `StateBackend`: seed files in, read them back out              |
| 06  | `06-real_filesystem`      | `FilesystemBackend`: editing real files safely                 |
| 07  | `07-shell_execute`        | `LocalShellBackend` and the `execute` tool                     |
| 08  | `08-composite_backend`    | `CompositeBackend`: route paths to different backends          |
| 09  | `09-subagents_basics`     | The `task` tool and context isolation                          |
| 10  | `10-custom_subagents`     | Per-subagent tools/models; `CompiledSubAgent`                  |
| 11  | `11-structured_output`    | `response_format` and `structured_response`                    |
| 12  | `12-checkpointer_threads` | Checkpointers, `thread_id`, multi-turn memory                  |
| 13  | `13-human_in_the_loop`    | `interrupt_on`, approve/reject/edit/respond                    |
| 14  | `14-permissions`          | `FilesystemPermission`: allow, deny, interrupt                 |
| 15  | `15-long_term_memory`     | `StoreBackend` + `memory=` across conversations                |
| 16  | `16-skills`               | `SKILL.md` packages and progressive disclosure                 |
| 17  | `17-streaming`            | `stream_mode="updates"` vs `"messages"`                        |
| 18  | `18-context_management`   | Automatic summarization of long conversations                  |
| 19  | `19-capstone_research`    | Everything combined: a research agent                          |
| 20  | `20-mcp_tools`            | MCP tools via `MultiServerMCPClient` (async)                   |

## Notes

- Episodes 06, 07 and 08 write to a `workspace/` folder inside their own directory (git-ignored).
- Every episode ships a 3-slide Marp deck (`slides.md` / `slides.html`) and a `diagrams/` folder
  of Mermaid sources with rendered `.svg`/`.png`.
- Every script is also a VS Code interactive notebook — the `# %%` markers let you run it cell by cell.
- Nothing here calls the internet except your model provider (and episode 20's local MCP subprocess).
