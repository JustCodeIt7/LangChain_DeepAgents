"""
Agent construction for DeepCoder.
=================================
Keeping this out of main.py means the REPL stays about talking to the user,
and this file stays about what the agent can DO.
"""

import config
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, LocalShellBackend, StateBackend
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver


def build_model():
    """Create the chat model with Ollama-specific tuning applied.

    Passing a model *instance* instead of the "ollama:..." string is what lets
    us set num_ctx and keep_alive. init_chat_model forwards unknown kwargs to
    the provider class, so these land on ChatOllama.
    """
    return init_chat_model(
        config.MODEL,
        num_ctx=config.NUM_CTX,
        keep_alive=config.KEEP_ALIVE,
    )


def build_backend() -> CompositeBackend:
    """Route file paths to real disk, except a scratch area kept in memory.

    CompositeBackend picks a backend per path prefix, longest match wins:
      /scratch/...  -> StateBackend, in-memory, vanishes with the process
      everything else -> LocalShellBackend, real files under WORKDIR

    The scratch route matters more than it looks: deepagents writes its own
    internal bookkeeping (large tool results, conversation history) through
    this same backend. Without the route, that machinery would litter your
    project directory with files you never asked for.

    LocalShellBackend is FilesystemBackend plus an `execute` tool. That single
    addition is what turns a file editor into a coding agent: it can now run
    the tests it just wrote.

    inherit_env=True is not optional in practice. The default env is EMPTY,
    which means no PATH -- so `python`, `git` and `npm` are all "command not
    found" and the failure looks like a broken agent rather than a config
    choice. The tradeoff is that your real environment (including secrets in
    env vars) is visible to whatever the model decides to run.
    """
    config.WORKDIR.mkdir(parents=True, exist_ok=True)
    return CompositeBackend(
        default=LocalShellBackend(
            root_dir=str(config.WORKDIR),
            inherit_env=True,
            timeout=config.SHELL_TIMEOUT,
        ),
        routes={"/scratch/": StateBackend()},
    )


def build_agent():
    """Assemble the agent: model + shell + memory.

    Note what is NOT here: interrupt_on. This part is about the stream and
    nothing else, and a pause the renderer cannot answer would just hang. The
    gates come back in Part 7, once the event layer can express them.
    """
    return create_deep_agent(
        model=build_model(),
        system_prompt=config.SYSTEM_PROMPT,
        backend=build_backend(),
        checkpointer=InMemorySaver(),
    )
