# 16 — Skills (Reusable Expertise on Demand)

## Overview
**Goal:** Load a `SKILL.md` package and watch progressive disclosure: the agent sees only the skill's name + description up front, and reads the full instructions only when the task calls for it.

## What You'll Learn
- **Skill layout**: a folder with a `SKILL.md` — YAML frontmatter (`name`, `description`) + markdown instructions
- **`skills=["/skills"]`**: registers the skills directory; only the frontmatter is injected into the system prompt
- **Progressive disclosure**: the body stays on disk until the agent decides it needs it — that is what keeps a library of 50 skills from blowing up the context window
- **Matching by description**: the episode never mentions the skill by name; the agent matches the request against the description on its own

## Key Concepts
1. **GOTCHA — skills are read THROUGH the agent's backend**, not off the host OS. The default `StateBackend` is virtual and cannot see your disk, so skills would silently never load. Use a real `FilesystemBackend` and give the path as the backend sees it (`/skills`), not as an OS path
2. Watch the tool calls: a `read_file` for `SKILL.md` BEFORE the answer is the skill being pulled in
3. The output follows the skill's house style (here: release-notes format)

## Run Instructions
```bash
cd deepagents_101/16-skills
python 16-skills.py

DEEPAGENTS_MODEL=openai:gpt-4.1-mini python 16-skills.py
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `DEEPAGENTS_MODEL` | `ollama:qwen3.5:9b` | Any LangChain provider string |

Provider keys go in the repo-root `.env`. Setup is in the [series README](../README.md).

## Notes
- Ships with `skills/release-notes/SKILL.md` (the skill) and `tmp/changes_v2.1.0.txt` (sample input).
