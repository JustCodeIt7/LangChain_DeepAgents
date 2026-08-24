---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 01 — Your First Deep Agent

*An accessible framework for LLM-powered agents with built-in support for complex, multi-step work*

---

# What is Deep Agents?

- An **accessible framework** for building LLM-powered agents
- Built on **LangChain**, running on the **LangGraph runtime**
- An **"agent harness"** — a reliable environment for:
  - Long-term memory
  - File system management
  - Delegation

---

# Core Architecture — Four Pillars

```mermaid
flowchart TB
    subgraph harness["Deep Agents — the agent harness (built on LangChain · LangGraph runtime)"]
        direction LR
        ee["Execution Environment<br/><br/>tools · virtual filesystem<br/>optional sandboxed code execution"] ~~~ cm["Context Management<br/><br/>memory · skill loading<br/>automatic summarization"] ~~~ del["Delegation<br/><br/>subagents<br/>structured task planning"] ~~~ steer["Steering<br/><br/>human-in-the-loop approvals<br/>declarative filesystem permission rules"]
    end
```

---

# Pillar 1 — Execution Environment

- Provides the **tools** the agent works with
- A **virtual file system** for data
- **Optional sandboxed code execution**
- Goal: agents interact **safely** with data and external systems

---

# Pillar 2 — Context Management

- **Memory**
- **Skill loading**
- **Automatic summarization**
- Keeps agents **efficient within token limits** while retaining critical information

---

# Pillar 3 — Delegation

- Breaks down **large tasks**
- Spawns **subagents**
- Uses **structured task planning tools**
- Better **accountability**

---

# Pillar 4 — Steering

- **Human oversight** built in
- **Human-in-the-loop approvals** for sensitive tool calls
- **Declarative filesystem permission rules**

---

# Key Capabilities

1. **Virtual Filesystem** — pluggable backends, configurable permission rules
2. **Skill & Memory Integration** — `SKILL.md` / `AGENTS.md` injected into context
3. **Advanced Context Optimization** — prompt caching + summarization
4. **Task Delegation** — isolated subagents with fresh contexts
5. **Human-in-the-loop** — real-time interrupts via LangGraph

---

# Virtual Filesystem

```mermaid
flowchart LR
    agent["Deep agent"] --> ops["File operations<br/>list · read · edit · search"]
    ops --> vfs["Virtual filesystem<br/>configurable permission rules"]
    vfs --> b1["Pluggable backend 1"]
    vfs --> b2["Pluggable backend 2"]
    vfs --> b3["Pluggable backend 3"]
```

- **Pluggable backends** for managing files
- Operations: **listing, reading, editing, searching**
- **Configurable permission rules**

---

# Skill & Memory Integration

- Standardized files: **`SKILL.md`** and **`AGENTS.md`**
- **Dynamically injects** domain knowledge into the agent's context
- Carries **persistent user preferences**

---

# Advanced Context Optimization

- **Prompt caching** → reduces **latency and costs**
- **Summarization** → prevents **context window saturation** during long-running tasks

```mermaid
flowchart TB
    task["Long-running task"] --> ctx
    subgraph ctx["Context management — stay within token limits"]
        direction LR
        mem["Memory<br/>persistent user preferences"]
        skills["Skill loading<br/>SKILL.md · AGENTS.md"]
        cache["Prompt caching<br/>reduces latency and cost"]
        sum["Automatic summarization<br/>prevents context window saturation"]
    end
    ctx --> out["Efficient agent<br/>critical information retained"]
```

---

# Task Delegation

```mermaid
sequenceDiagram
    participant U as User
    participant A as Main agent
    participant S as Subagent
    U->>A: large task
    A->>A: break down with structured task planning
    A->>S: offload heavy subtask
    Note over S: fresh, independent context
    S-->>A: final result
    A-->>U: answer
```

- Main agent **offloads heavy subtasks** to isolated subagents
- Subagents operate in **fresh, independent contexts**
- They **return final results** upon completion

---

# Human-in-the-Loop

```mermaid
sequenceDiagram
    participant A as Agent
    participant L as LangGraph runtime
    participant H as Human
    A->>L: sensitive tool call
    L->>H: real-time interrupt
    H-->>L: approve / reject
    L-->>A: resume execution
```

- Integrates with **LangGraph**
- **Real-time interrupts**
- Developers keep control over **critical decision-making points**

---

# In Summary

Deep Agents lets you build agents that:

- Perform **complex, multi-step tasks**
- Handle **persistent memory**
- Enforce **strict file access controls**
- **Decompose massive projects** into manageable subtasks

A **highly customizable and scalable** solution for modern AI applications.
