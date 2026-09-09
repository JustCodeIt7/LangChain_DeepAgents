---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 16 — Skills

*A folder with a `SKILL.md` — the agent reads the whole thing only when it needs to*

---

# The Package and the Gotcha

```
skills/
  release-notes/
    SKILL.md      # YAML frontmatter (name, description) + markdown instructions
```

```python
backend = FilesystemBackend(root_dir=str(EPISODE_DIR), virtual_mode=True)
agent = create_deep_agent(model=MODEL, backend=backend, skills=["/skills"])
```

- ⚠️ Skills are read **through the backend**, not off the host OS
- The default `StateBackend` cannot see your disk — skills would **silently never load**
- Give the path **as the backend sees it** (`/skills`), not as an OS path

---

# Progressive Disclosure

1. Only **name + description** from the frontmatter go into the system prompt
2. The agent matches your request against that description — you never name the skill
3. It calls `read_file` on `SKILL.md` **only once it decides the skill applies**
4. The body then steers the output's house style

That step-3 read is what keeps a library of 50 skills from blowing up your context window.

**Next (ep. 17):** streaming — progress UIs vs token-by-token chat.
