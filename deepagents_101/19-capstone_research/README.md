# 19 — Capstone: A Research Agent

## Overview
**Goal:** Everything from the series in one agent: planning (ep. 04) + virtual filesystem (ep. 05) + a specialist subagent (ep. 09) + live streaming (ep. 17). It researches a local corpus and writes a report file. No internet required.

## What You'll Learn
- **Seeding a corpus**: the agent's "world" is a set of local files built with `create_file_data` — in a real research agent these would be web pages or PDFs; keeping them local makes the episode fast, free, and reproducible
- **A specialist subagent**: the `analyst` reads one source and reports back; because subagents have isolated context, the long file contents never clog the orchestrator's history — only the short summary comes back
- **Planning + streaming together**: `TodoListMiddleware` for the plan, `stream(stream_mode="updates")` to watch tool calls as they happen
- **The deliverable**: the final report is a file in the returned state — `final_state["files"]["/report.md"]`

## Key Concepts
1. This is the reference architecture for a "research agent": plan → delegate source-reading to subagents → synthesize into a file
2. The orchestrator's context stays small by design — that is what makes the pattern scale
3. No network calls: the model provider is the only external dependency

## Run Instructions
```bash
cd deepagents_101/19-capstone_research
python 19-capstone_research.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 19-capstone_research.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
