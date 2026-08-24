# 11 — Structured Output

## Overview
**Goal:** Get typed, validated results from the agent by passing a Pydantic model as `response_format` — no more regex-parsing the model's prose.

## What You'll Learn
- **`response_format=BookReview`**: attach a Pydantic model to the agent and read the result from `result["structured_response"]` — a real object, not a string
- **`Field(description=...)` acts as per-field instructions**: descriptions are sent to the model as part of the schema
- **Free validation + serialization**: `review.model_dump_json()` is ready for an API or database
- **Failing gracefully**: smaller local models sometimes drift off the schema — catch the error and suggest a larger model instead of crashing

## Key Concepts
1. Keep schemas flat and simple — a few scalar fields are far more reliable on small models than deep nesting
2. The task should fit the schema (a book review for a `BookReview` model)
3. Structured output rides on the model following a tool/JSON schema — it's a contract, not a guarantee

## Run Instructions
```bash
cd deepagents_101/11-structured_output
python 11-structured_output.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 11-structured_output.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
