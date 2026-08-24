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

## Teaching Notes

**Hook:** "Pass a Pydantic model and get a typed object back — no more regex-parsing the model's prose."

**Walk the cells:**

- **Step 2 — Describe the shape:** `Field(description=...)` is sent to the model as part of the schema — it acts as per-field instructions. Keep schemas flat.
- **Step 3 — Attach the schema:** `response_format=BookReview`.
- **Step 4 — Ask a question that fits:** Wrapped in try/except — small models sometimes drift off the schema; fail gracefully.
- **Step 5 — Use it like a Python object:** Attribute access, then `model_dump_json()`.

**On camera:**

- The star-rating line (★★★★☆) is a nice visual. Show the JSON output — "ready for an API or database."

**If it goes wrong:**

- A small local model may not produce valid structured output. The script prints a red message and suggests a larger model — have that fallback line ready.

**Bridge to ep. 12:** "Structured output is great for one run. What about remembering across runs? Next: checkpointers and threads."

## Run Instructions

```bash
cd deepagents_101/11-structured_output
python 11-structured_output.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 11-structured_output.py
```

## Environment Variables

| Variable           | Default             | Description                   |
| ------------------ | ------------------- | ----------------------------- |
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:2b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).
