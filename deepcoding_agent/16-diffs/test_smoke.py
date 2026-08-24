"""
Headless UI test. No model, no terminal, no Ollama.
===================================================
Covers the approval modal, including the case that breaks naive
implementations: one pause carrying TWO pending actions.

Run:  python -m pytest test_smoke.py -q -p anyio
"""

import pytest
from textual.widgets import Markdown
from tui import DeepCoderApp


@pytest.fixture
def anyio_backend() -> str:
    """anyio ships a pytest plugin, so no extra test dependency is needed."""
    return "asyncio"


class Interrupt:
    """Mimics a LangGraph Interrupt carrying a batch of pending actions."""

    def __init__(self, actions):
        self.value = {"action_requests": actions}


class PlanningAgent:
    """Emits a todo list, a nested subagent tool call, then a short answer.

    Chunks are (namespace, mode, payload) 3-tuples now that the app streams
    with subgraphs=True. An empty namespace means "the main agent".
    """

    def stream(self, payload, config=None, stream_mode=None, subgraphs=False):
        from langchain_core.messages import AIMessageChunk

        yield ((), "updates", {"tools": {"todos": [
            {"content": "read the file", "status": "completed"},
            {"content": "fix the bug", "status": "in_progress"},
        ]}})
        nested_call = type("M", (), {"tool_calls": [
            {"id": "n1", "name": "read_file", "args": {"file_path": "/a.py"}}
        ]})()
        yield (("tools:abc",), "updates", {"model": {"messages": [nested_call]}})
        yield ((), "messages", (AIMessageChunk(content="planned"), {}))


class GatedAgent:
    """Pauses once with two actions, then answers after being resumed."""

    ACTIONS = [
        {"name": "write_file", "args": {"file_path": "/a.txt", "content": "hello"}},
        {"name": "execute", "args": {"command": "echo hi"}},
    ]

    def __init__(self) -> None:
        self.decisions: list[dict] | None = None

    def stream(self, payload, config=None, stream_mode=None, subgraphs=False):
        from langchain_core.messages import AIMessageChunk

        if self.decisions is None:  # first pass: pause for approval
            self.decisions = []
            yield ((), "updates", {"__interrupt__": (Interrupt(self.ACTIONS),)})
            return
        for token in ("all ", "done"):
            yield ((), "messages", (AIMessageChunk(content=token), {}))

    def resumed_with(self, command) -> None:
        self.decisions = command.resume["decisions"]


def rendered(app) -> list[str]:
    """Text of every Markdown widget currently in the chat log."""
    return [str(widget._markdown) for widget in app.query(Markdown)]


@pytest.mark.anyio
async def test_modal_lists_every_pending_action() -> None:
    """A batched pause must show BOTH actions, not just the first."""
    app = DeepCoderApp(agent=GatedAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"go")
        await pilot.press("enter")
        for _ in range(60):
            await pilot.pause()
            if app.screen.__class__.__name__ == "ApprovalScreen":
                break

        assert app.screen.__class__.__name__ == "ApprovalScreen"
        assert len(app.screen.actions) == 2
        assert len(app.screen.query(".action")) == 2


@pytest.mark.anyio
async def test_always_fills_the_allowlist() -> None:
    """Pressing 'a' should remember both tool names for the session."""
    app = DeepCoderApp(agent=GatedAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"go")
        await pilot.press("enter")
        for _ in range(60):
            await pilot.pause()
            if app.screen.__class__.__name__ == "ApprovalScreen":
                break

        await pilot.press("a")
        await pilot.pause()
        assert app.allowlist == {"write_file", "execute"}


@pytest.mark.anyio
async def test_plan_panel_shows_todos() -> None:
    """A todos update in the stream should reveal and fill the sidebar."""
    from widgets import PlanPanel

    app = DeepCoderApp(agent=PlanningAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"go")
        await pilot.press("enter")
        await app.workers.wait_for_complete()
        for _ in range(4):
            await pilot.pause()

        panel = app.query_one("#plan", PlanPanel)
        assert panel.display is True
        text = str(panel.content)
        assert "fix the bug" in text


@pytest.mark.anyio
async def test_slash_commands_never_reach_the_agent() -> None:
    """/help renders locally; /new resets the thread id."""
    app = DeepCoderApp(agent=PlanningAgent())
    async with app.run_test() as pilot:
        old_thread = app.thread_id
        await pilot.press(*"/help")
        await pilot.press("enter")
        await pilot.pause()
        assert any("/model" in line for line in rendered(app))

        await pilot.press(*"/new")
        await pilot.press("enter")
        await pilot.pause()
        assert app.thread_id != old_thread


@pytest.mark.anyio
async def test_resume_picker_opens_and_closes() -> None:
    """/resume shows the picker; escape dismisses it without changes."""
    app = DeepCoderApp(agent=PlanningAgent())
    async with app.run_test() as pilot:
        thread_before = app.thread_id
        await pilot.press(*"/resume")
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "ResumeScreen"

        await pilot.press("escape")
        await pilot.pause()
        assert app.thread_id == thread_before


@pytest.mark.anyio
async def test_subagent_work_renders_indented() -> None:
    """Events from inside a subagent get the nested (indented) style."""
    app = DeepCoderApp(agent=PlanningAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"go")
        await pilot.press("enter")
        await app.workers.wait_for_complete()
        for _ in range(4):
            await pilot.pause()
        nested = app.query(".nested")
        assert len(nested) == 1
        assert "read_file" in str(nested[0]._markdown)


@pytest.mark.anyio
async def test_init_command_starts_an_agent_turn() -> None:
    """/init is a command that SENDS a prompt rather than printing text."""
    app = DeepCoderApp(agent=PlanningAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"/init")
        await pilot.press("enter")
        await app.workers.wait_for_complete()
        for _ in range(4):
            await pilot.pause()
        # The synthetic prompt shows up as a user message mentioning AGENTS.md.
        assert any("AGENTS.md" in line for line in rendered(app))


@pytest.mark.anyio
async def test_modal_shows_a_diff_for_writes() -> None:
    """write_file actions come with a rendered unified diff."""
    app = DeepCoderApp(agent=GatedAgent())
    async with app.run_test() as pilot:
        await pilot.press(*"go")
        await pilot.press("enter")
        for _ in range(60):
            await pilot.pause()
            if app.screen.__class__.__name__ == "ApprovalScreen":
                break

        diffs = app.screen.query(".diff")
        assert len(diffs) == 1  # write_file gets one; execute does not
