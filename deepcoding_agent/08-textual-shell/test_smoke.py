"""
Headless UI test. No model, no terminal, no Ollama.
===================================================
App.run_test() drives the real app through a Pilot, so this catches broken
layout and wiring in about a second.

Run:  python -m pytest test_smoke.py -q
"""

import pytest
from textual.widgets import Markdown
from tui import DeepCoderApp


@pytest.fixture
def anyio_backend() -> str:
    """anyio ships a pytest plugin, so no extra test dependency is needed."""
    return "asyncio"


class StubAgent:
    """Stands in for the real agent, yielding one canned assistant reply."""

    def stream(self, payload, config=None, stream_mode=None):
        from langchain_core.messages import AIMessageChunk

        yield ("messages", (AIMessageChunk(content="stub answer"), {}))


@pytest.mark.anyio
async def test_ask_renders_both_messages() -> None:
    """Typing a question should add the user line and the assistant reply."""
    app = DeepCoderApp(agent=StubAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"hello")
        await pilot.press("enter")
        await pilot.pause()

        rendered = [str(w._markdown) for w in app.query(Markdown)]
        assert any("hello" in text for text in rendered), rendered
        assert any("stub answer" in text for text in rendered), rendered
