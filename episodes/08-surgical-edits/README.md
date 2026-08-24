# Episode 8 — Surgical Edits: `edit_file` + the Fuzzy Fallback Wrapper

## Overview

**Length:** ~25 minutes  
**Goal:** Move from whole-file rewrites to precise search-replace edits using a teaching wrapper that provides fuzzy matching and helpful error messages.

## What You'll Learn

- **Search-replace editing**: The edit format used by Aider, Codex, and Cline — find exact text and replace it in-place
- **`edit_file_safe(path, search, replace)`**: A custom tool with three tiers of behavior: exact match → fuzzy match (≥90% similarity) → unified diff on total failure so the model self-corrects
- **Error resilience**: How to provide actionable feedback when an edit fails, including showing a diff so the model can adjust its next attempt

## Key Concepts

1. Whole-file rewrites are wasteful and error-prone; surgical edits modify only the lines that need changing
2. `difflib.SequenceMatcher` provides fuzzy matching — if the exact search string isn't found (e.g., due to whitespace differences), a close match may still work
3. On total failure, returning a unified diff helps the model understand what went wrong and adjust its approach
4. All edits go through the approval gate from Episode 6 — destructive file modifications require explicit user consent

## Run Instructions

```bash
# Create workspace with a sample file:
mkdir -p ./workspace
echo "def hello():\n    print('some content')\n\nhello()" > ./workspace/big.py

# Ask the agent to make a surgical edit:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 08-surgical-edits.py "In big.py, change 'some content' to 'EDITED'. Use edit_file_safe."

# Verify the change:
cat ./workspace/big.py
```

## Prerequisites

```bash
pip install deepagents langchain-ollama rich python-dotenv
```
