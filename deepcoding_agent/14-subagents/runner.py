"""
The event layer: one agent turn, streamed as small typed events.
================================================================
Everything the UI needs to know arrives here as an Event. The CLI renders
these by printing them; from Part 7 onward the Textual app renders the exact
same events as widgets. Nothing in this file knows which UI it is feeding.

This is a plain SYNCHRONOUS generator on purpose. It works in a `for` loop
today and inside a Textual thread worker later, without changing shape.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from langgraph.types import Command


# %% Step 1: The events
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
class ApprovalNeeded:
    """The run paused. Every pending action must get a decision, in order."""

    actions: list[dict[str, Any]]


@dataclass
class Plan:
    """The agent wrote or revised its todo list."""

    todos: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Done:
    """The turn finished. `usage` is token counts when the provider reports them."""

    text: str
    usage: dict[str, int] | None = None


@dataclass
class Failed:
    """The turn raised. The message is already human-readable."""

    error: str


Event = Token | ToolStart | Plan | ApprovalNeeded | Done | Failed


# %% Step 2: Reading the raw stream
def _tool_starts(update: Any, seen: set[str]) -> Iterator[ToolStart]:
    """Pull tool calls out of one 'updates' chunk, skipping repeats.

    The same AI message can appear in the stream more than once -- notably
    when a turn pauses for approval and then resumes, replaying the message
    that requested the tool. Every tool call carries a stable id, so we use
    that to announce each one exactly once.
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

    `payload` is a message dict, or a resume Command after a pause. Pass the
    same `seen` set across a pause and its resume so a tool call is announced
    once, not once per resume.
    """
    answer: list[str] = []
    usage: dict[str, int] | None = None
    seen = seen if seen is not None else set()

    try:
        # subgraphs=True surfaces what SUBAGENTS do. Every chunk now arrives
        # as a 3-tuple: (namespace, mode, payload). The namespace is () for
        # the main agent and ("tools:<id>",) inside a delegated task.
        for namespace, mode, data in agent.stream(
            payload, config=config, stream_mode=["updates", "messages"], subgraphs=True
        ):
            nested = bool(namespace)
            if mode == "updates":
                for node_update in data.values():
                    yield from _tool_starts(node_update, seen, nested)
                    # TodoListMiddleware puts the plan in state under "todos".
                    if isinstance(node_update, dict) and node_update.get("todos"):
                        yield Plan(todos=node_update["todos"])
                # A pause is delivered as an "__interrupt__" entry.
                interrupts = data.get("__interrupt__")
                if interrupts:
                    yield ApprovalNeeded(actions=interrupts[0].value["action_requests"])
                    return

            elif mode == "messages":
                # This mode yields (chunk, metadata) tuples.
                chunk, meta = data
                if nested or meta.get("lc_source") == "summarization":
                    continue  # subagent chatter and internals are not the answer
                text = _token_text(chunk)
                if text:
                    answer.append(text)
                    yield Token(text)
                if getattr(chunk, "usage_metadata", None):
                    usage = chunk.usage_metadata

    except Exception as error:  # noqa: BLE001 - the UI decides how to show it
        yield Failed(error=f"{type(error).__name__}: {error}")
        return

    yield Done(text="".join(answer).strip(), usage=usage)


def resume_with(decisions: list[dict]) -> Command:
    """Build the resume payload for run_turn after an ApprovalNeeded.

    The list must line up one-to-one with the actions you were given.
    """
    return Command(resume={"decisions": decisions})
