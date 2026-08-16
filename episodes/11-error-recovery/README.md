# Episode 11 — Error Recovery: Self-Healing Loops

## Overview
**Length:** ~35 minutes  
**Goal:** Build an agent that writes code, runs tests, reads failures, and fixes them autonomously — up to a retry cap. The "wow" episode where the agent heals itself.

## What You'll Learn
- **`run_tests(path)`**: A custom `@tool` that executes `pytest` in the workspace, captures pass/fail output, and returns a readable summary string
- **Retry loop pattern**: Implementing recovery as a Python loop *around* the Deep Agents graph — after each run, if tests fail, re-invoke with failure output appended to the conversation
- **Failure detection heuristic**: Looking for `[exit 1]` + `FAILED` or `Error` in tool messages to decide whether to retry

## Key Concepts
1. Self-healing is implemented as a loop around `.invoke()`, not as a new graph node — you don't fight the framework, you orchestrate it from outside
2. The agent writes code → runs tests → reads failure output → fixes the bug → re-runs — all automatically until success or retry cap
3. Failure detection uses simple heuristics (exit codes + error keywords); tighten these if you see false recoveries in your demo
4. **Model size matters**: recovery is unreliable on small local models (≤8B) — use 32b+ or OpenAI for reliable self-correction

## Run Instructions
```bash
# Create workspace with a failing test:
mkdir -p ./workspace/tests
echo "def add(a, b):\n    return a - b  # Bug: should be +" > ./workspace/main.py
echo "from main import add\ndef test_add():\n    assert add(2, 3) == 5" > ./workspace/tests/test_main.py

# Ask the agent to fix failing tests autonomously:
CODEIT_WORKDIR=./workspace LLM_PROVIDER=openai OPENAI_API_KEY=your-key \
    python 11-error-recovery.py "Run the tests. If they fail, read the failure and fix the code."

# Or with a large local model:
LLM_MODEL=qwen2.5-coder:32b CODEIT_WORKDIR=./workspace LLM_PROVIDER=ollama \
    python 11-error-recovery.py "Run the tests. If they fail, read the failure and fix the code."
```

## Prerequisites
```bash
pip install deepagents langchain-ollama rich python-dotenv pytest
```