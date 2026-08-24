"""
Sessions that survive a restart.
================================
Two pieces, both living in .deepcoder/ inside your workdir:
  sessions.db    -- SqliteSaver: every turn of every thread, checkpointed
  threads.json   -- our own tiny index: thread_id -> title + timestamp

LangGraph gives us the first for free. The second exists because a
checkpointer can REPLAY a thread but cannot LIST them nicely -- a resume
picker needs titles, so we keep our own.
"""

import json
import sqlite3
import time
from pathlib import Path

import config
from langgraph.checkpoint.sqlite import SqliteSaver


def _home() -> Path:
    """The .deepcoder/ directory, created on first use."""
    home = config.WORKDIR / ".deepcoder"
    home.mkdir(parents=True, exist_ok=True)
    return home


def open_checkpointer() -> SqliteSaver:
    """A SqliteSaver backed by a real file instead of RAM.

    check_same_thread=False because the agent runs in a worker thread while
    Textual owns the main one; sqlite allows that as long as we do not share
    a transaction across threads, and the saver serializes its own writes.
    """
    connection = sqlite3.connect(_home() / "sessions.db", check_same_thread=False)
    return SqliteSaver(connection)


# %% The thread index
def _index_path() -> Path:
    return _home() / "threads.json"


def load_index() -> dict[str, dict]:
    """thread_id -> {"title": ..., "updated": ...}, newest first."""
    try:
        entries = json.loads(_index_path().read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return dict(sorted(entries.items(), key=lambda kv: -kv[1].get("updated", 0)))


def remember(thread_id: str, first_message: str) -> None:
    """Record a thread the first time it gets a message; bump it after."""
    entries = load_index()
    entry = entries.setdefault(thread_id, {"title": first_message[:60]})
    entry["updated"] = int(time.time())
    _index_path().write_text(json.dumps(entries, indent=2))


def history(agent, thread_id: str) -> list[tuple[str, str]]:
    """(role, text) pairs for a stored thread, oldest first.

    get_state() returns the latest checkpoint; its "messages" list is the
    whole conversation, which is all a chat log needs to redraw itself.
    """
    state = agent.get_state({"configurable": {"thread_id": thread_id}})
    pairs: list[tuple[str, str]] = []
    for message in state.values.get("messages", []):
        role = getattr(message, "type", "")
        content = message.content if isinstance(message.content, str) else ""
        if role in ("human", "ai") and content.strip():
            pairs.append(("you" if role == "human" else "deepcoder", content.strip()))
    return pairs
