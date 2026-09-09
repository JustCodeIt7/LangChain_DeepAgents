"""
The event layer: one agent turn, streamed as small typed events.
================================================================
Everything the UI needs arrives here as an Event. The CLI prints them; from
Part 8 the Textual app renders the same events as widgets. Nothing in this
file knows which UI it feeds.

Synchronous on purpose: it works in a `for` loop today and inside a Textual
thread worker later, without changing shape.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


# %% Step 1: The events
# Five small facts a UI might want to show. Nothing else crosses this line.
@dataclass
class Token:
    """A piece of the assistant's answer, as it is generated."""
    text: str


@dataclass
class ToolStart:
    """The agent began calling a tool."""
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class Done:
    """The turn finished. `usage` is token counts, when reported."""
    text: str
    usage: dict[str, int] | None = None


Event = Token | ToolStart | Done


# %% Step 2: Reading the raw stream
def _tool_starts(update: Any, seen: set[str]) -> Iterator[ToolStart]:
    """Pull tool calls out of one 'updates' chunk, skipping repeats.

    The same AI message can appear more than once, so key on the call id.
    """
    if not isinstance(update, dict):
        return
    for message in update.get("messages", []) or []:
        for call in getattr(message, "tool_calls", []) or []:
            call_id = call.get("id") or f"{call.get('name')}:{call.get('args')}"
            if call_id in seen:
                continue
            seen.add(call_id)
            yield ToolStart(name=call.get("name", "?"), args=call.get("args", {}) or {})


def _token_text(chunk: Any) -> str:
    """Text of an assistant chunk, or "" if it is anything else."""
    if chunk.__class__.__name__ != "AIMessageChunk":
        return ""
    content = chunk.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


# %% Step 3: One turn, as events
def run_turn(agent, payload, config: dict, seen: set[str] | None = None) -> Iterator[Event]:
    """Stream one turn as events.

    Two stream modes at once. "updates" gives one chunk per graph step (where
    tool calls show up); "messages" gives token-by-token text. With a list of
    modes, each chunk arrives as (mode_name, payload).
    """
    answer: list[str] = []
    usage: dict[str, int] | None = None
    seen = seen if seen is not None else set()

    for mode, data in agent.stream(payload, config=config, stream_mode=["updates", "messages"]):
        if mode == "updates":
            for node_update in data.values():
                yield from _tool_starts(node_update, seen)

        elif mode == "messages":
            # This mode yields (chunk, metadata) tuples.
            chunk, meta = data
            if meta.get("lc_source") == "summarization":
                continue  # internal machinery, not the user's answer
            text = _token_text(chunk)
            if text:
                answer.append(text)
                yield Token(text)
            if getattr(chunk, "usage_metadata", None):
                usage = chunk.usage_metadata

    yield Done(text="".join(answer).strip(), usage=usage)
