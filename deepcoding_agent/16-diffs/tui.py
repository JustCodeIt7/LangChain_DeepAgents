"""
The Textual app shell.
======================
The agent runs on a WORKER THREAD. The worker never touches a widget -- it
posts messages, and the app updates the UI when it receives them.

When a turn pauses for approval, the worker blocks on call_from_thread until
the modal returns a decision for every pending action.
"""

import time

import config
import runner
import sessions
from agent import build_agent
from commands import Commands
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.suggester import SuggestFromList
from textual.widgets import Footer, Header, Input, Markdown, Static
from textual.worker import get_current_worker
from widgets import ApprovalScreen, PlanPanel, ResumeScreen


# %% Step 1: Messages the worker sends back to the UI
class Chunk(Message):
    """Some text arrived for the answer in progress."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class ToolLine(Message):
    """The agent started a tool. Nested = inside a subagent."""

    def __init__(self, label: str, nested: bool = False) -> None:
        super().__init__()
        self.label = label
        self.nested = nested


class PlanUpdate(Message):
    """The agent revised its todo list."""

    def __init__(self, todos: list[dict]) -> None:
        super().__init__()
        self.todos = todos


class Finished(Message):
    """The turn ended, successfully or not."""

    def __init__(self, error: str | None = None, usage: dict | None = None) -> None:
        super().__init__()
        self.error = error
        self.usage = usage or {}


class DeepCoderApp(App):
    """The DeepCoder terminal UI."""

    CSS_PATH = "app.tcss"
    TITLE = "DeepCoder"
    BINDINGS = [("escape", "cancel", "Cancel turn")]

    def __init__(self, agent=None, thread_id: str = "tui") -> None:
        super().__init__()
        self.agent = agent if agent is not None else build_agent()
        self.thread_id = thread_id
        self.answer: Markdown | None = None  # the reply being streamed
        self.buffer = ""
        self.dirty = False  # is there new text the timer has not painted yet?
        self.allowlist: set[str] = set()  # tools the user said "always" to
        self.tokens = 0        # running token total for the session
        self.started = 0.0     # when the current turn began
        self.commands = Commands(self)

    # %% Step 2: Lay out the screen
    def compose(self) -> ComposeResult:
        """Build the widget tree, top to bottom."""
        yield Header()
        with Horizontal(id="body"):
            yield VerticalScroll(id="chat")
            yield PlanPanel(id="plan")
        yield Input(
            placeholder="Ask DeepCoder…  (/help for commands, esc cancels)",
            id="prompt",
            suggester=SuggestFromList(self.commands.names()),
        )
        yield Static(config.describe(), id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the input and start the repaint timer."""
        self.query_one("#prompt", Input).focus()
        self.query_one("#plan", PlanPanel).display = False
        # ~20 fps is smoother than the eye needs and costs almost nothing.
        self.set_interval(1 / 20, self.repaint)
        self.set_interval(1 / 2, self.refresh_status)

    def add(self, markdown: str, css_class: str) -> Markdown:
        """Append a widget to the chat log and scroll to it."""
        chat = self.query_one("#chat", VerticalScroll)
        widget = Markdown(markdown, classes=css_class)
        chat.mount(widget)
        chat.scroll_end(animate=False)
        return widget

    # %% Step 3: Submit -> start a worker
    @on(Input.Submitted, "#prompt")
    def submit(self, event: Input.Submitted) -> None:
        """Hand the question to a background thread and return immediately."""
        question = event.value.strip()
        if not question:
            return
        event.input.value = ""

        if question.startswith("/"):
            # Commands are for the user; the model never sees them.
            output = self.commands.run(question)
            if output:
                self.add(output, "tool")
            return
        self.send(question)

    def send(self, question: str) -> None:
        """Start an agent turn. Commands like /init reuse this entry point."""
        sessions.remember(self.thread_id, question)
        self.add(f"**you** — {question}", "user")
        self.buffer = ""
        self.dirty = False
        # The answer widget is created lazily, on the first token, so tool
        # lines that arrive first appear ABOVE the reply rather than below it.
        self.answer = None
        self.started = time.monotonic()
        self.run_turn(question)

    @work(thread=True, exclusive=True)
    def run_turn(self, question: str) -> None:
        """Runs OFF the UI thread. Must not touch widgets -- only post messages."""
        worker = get_current_worker()
        config_dict = {"configurable": {"thread_id": self.thread_id}}
        payload = {"messages": [{"role": "user", "content": question}]}
        seen: set[str] = set()  # shared across pauses: announce each tool once
        turn_usage: dict | None = None

        while True:
            pending: list[dict] | None = None

            for event in runner.run_turn(self.agent, payload, config_dict, seen):
                # Cancellation is checked BETWEEN events. If the model is
                # mid-call we cannot interrupt it; we stop at the next chunk.
                if worker.is_cancelled:
                    return
                match event:
                    case runner.Token(text=text):
                        self.post_message(Chunk(text))
                    case runner.ToolStart(name=name, args=args, nested=nested):
                        self.post_message(ToolLine(summarize(name, args), nested))
                    case runner.Plan(todos=todos):
                        self.post_message(PlanUpdate(todos))
                    case runner.Done(usage=usage):
                        # Remember: never touch app state from the worker.
                        # The count rides back on the Finished message.
                        turn_usage = usage
                    case runner.ApprovalNeeded(actions=actions):
                        pending = actions
                    case runner.Failed(error=error):
                        self.post_message(Finished(error=error))
                        return

            if pending is None:
                self.post_message(Finished(usage=turn_usage))
                return
            payload = runner.resume_with(self.ask_permission(pending))

    def pick_thread(self) -> None:
        """Open the resume picker; replay the chosen conversation."""

        def chosen(thread_id: str | None) -> None:
            if not thread_id:
                return
            self.thread_id = thread_id
            chat = self.query_one("#chat", VerticalScroll)
            chat.remove_children()
            # Replay from the checkpoint so the log shows the whole history.
            for role, text in sessions.history(self.agent, thread_id):
                self.add(f"**{role}** — {text}" if role == "you" else text,
                         "user" if role == "you" else "assistant")

        self.push_screen(ResumeScreen(sessions.load_index()), chosen)

    def ask_permission(self, actions: list[dict]) -> list[dict]:
        """Block this worker thread until the human answers the modal.

        call_from_thread runs the coroutine on the UI thread and hands the
        result back here. It is the one sanctioned way for a worker to ask
        the interface a question and wait for the answer.
        """
        if all(action.get("name") in self.allowlist for action in actions):
            return [{"type": "approve"} for _ in actions]
        return self.call_from_thread(self.push_screen_wait, ApprovalScreen(actions))

    # %% Step 4: Receive worker messages, back on the UI thread
    def on_chunk(self, message: Chunk) -> None:
        """Buffer streamed text. A timer does the actual repaint.

        Markdown.update() returns an awaitable that re-parses the document.
        Calling it once per token makes those calls race, and tokens get
        dropped -- the widget can end up showing only the first word. So we
        only ever collect text here, and repaint on a timer (below), which is
        both correct and far cheaper than parsing Markdown per token.
        """
        self.buffer += message.text
        self.dirty = True

    def repaint(self) -> None:
        """Render whatever has arrived since the last repaint."""
        if not self.dirty:
            return
        self.dirty = False
        if self.answer is None:
            self.answer = self.add(self.buffer, "assistant")
        else:
            self.answer.update(self.buffer)
        self.query_one("#chat", VerticalScroll).scroll_end(animate=False)

    def on_tool_line(self, message: ToolLine) -> None:
        """Show a tool call as its own dim line; indent subagent work."""
        prefix = "· " if message.nested else ""
        self.add(f"{prefix}`{message.label}`", "tool nested" if message.nested else "tool")

    def on_plan_update(self, message: PlanUpdate) -> None:
        """Redraw the plan panel."""
        self.query_one("#plan", PlanPanel).show(message.todos)

    def refresh_status(self) -> None:
        """Keep the status line current: model, workdir, elapsed, tokens."""
        busy = any(w.is_running for w in self.workers)
        elapsed = f"{time.monotonic() - self.started:4.1f}s" if busy else "idle"
        self.query_one("#status", Static).update(
            f"{config.MODEL}  |  {config.WORKDIR.name}/  |  {elapsed}  |  {self.tokens} tokens"
        )

    def on_finished(self, message: Finished) -> None:
        """Flush the last text, then tidy up."""
        self.repaint()  # the timer may not have fired since the final token
        self.tokens += message.usage.get("total_tokens", 0)
        if message.error:
            self.add(f"**error:** {message.error}", "assistant")
        elif not self.buffer.strip():
            self.add("_(done — no closing message)_", "assistant")
        self.answer = None

    def action_cancel(self) -> None:
        """Escape asks the running worker to stop."""
        for worker in self.workers:
            worker.cancel()
        if self.answer is not None:
            self.answer.update(self.buffer + "\n\n_(cancelled)_")
            self.answer = None


def summarize(name: str, args: dict) -> str:
    """One readable line describing what the agent is doing."""
    if name == "task":
        return f"task → {args.get('subagent_type', '?')}: {args.get('description', '')[:40]}"
    if name == "execute":
        return f"run: {args.get('command', '')}"
    path = args.get("file_path") or args.get("path") or ""
    return f"{name}: {path}" if path else name
