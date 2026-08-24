"""
Headless UI test. No model, no terminal, no Ollama.
===================================================
App.run_test() drives the real app through a Pilot, so this catches broken
layout and wiring in about a second.

Run:  python -m pytest test_smoke.py -q -p anyio
"""

import pytest
from textual.widgets import Markdown
from tui import DeepCoderApp


@pytest.fixture
def anyio_backend() -> str:
    """anyio ships a pytest plugin, so no extra test dependency is needed."""
    return "asyncio"


class StubAgent:
    """Stands in for the real agent: one tool call, then a short reply."""

    def stream(self, payload, config=None, stream_mode=None):
        from langchain_core.messages import AIMessageChunk

        message = type("M", (), {"tool_calls": [{"id": "1", "name": "ls", "args": {}}]})()
        yield ("updates", {"node": {"messages": [message]}})
        for token in ("stub ", "answer"):
            yield ("messages", (AIMessageChunk(content=token), {}))


def rendered(app) -> list[str]:
    """Text of every Markdown widget currently in the chat log."""
    return [str(widget._markdown) for widget in app.query(Markdown)]


@pytest.mark.anyio
async def test_worker_streams_into_the_ui() -> None:
    """A question should produce a user line, a tool line and the answer."""
    app = DeepCoderApp(agent=StubAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"hello")
        await pilot.press("enter")
        # Wait for the worker to finish, then let its last messages drain.
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.pause()

        text = rendered(app)
        assert any("hello" in line for line in text), text
        assert any("ls" in line for line in text), text
        assert any("stub answer" in line for line in text), text


@pytest.mark.anyio
async def test_ui_stays_responsive_during_a_turn() -> None:
    """The input must still accept keystrokes while the worker runs."""
    app = DeepCoderApp(agent=StubAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"first")
        await pilot.press("enter")
        await pilot.press(*"typed")  # would be swallowed if the UI blocked
        assert app.query_one("#prompt").value == "typed"
