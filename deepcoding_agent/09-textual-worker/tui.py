"""
The Textual app shell.
======================
The agent now runs on a WORKER THREAD. The worker never touches a widget --
it posts messages, and the app updates the UI when it receives them. That is
the whole rule for thread safety in Textual.
"""

import config
import runner
from agent import build_agent
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import Footer, Header, Input, Markdown, Static
from textual.worker import get_current_worker


# %% Step 1: Messages the worker sends back to the UI
class Chunk(Message):
    """Some text arrived for the answer in progress."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class ToolLine(Message):
    """The agent started a tool."""

    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label


class Finished(Message):
    """The turn ended, successfully or not."""

    def __init__(self, error: str | None = None) -> None:
        super().__init__()
        self.error = error


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

    # %% Step 2: Lay out the screen
    def compose(self) -> ComposeResult:
        """Build the widget tree, top to bottom."""
        yield Header()
        yield VerticalScroll(id="chat")
        yield Input(placeholder="Ask DeepCoder…  (esc cancels, ctrl+c quits)", id="prompt")
        yield Static(config.describe(), id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the input and start the repaint timer."""
        self.query_one("#prompt", Input).focus()
        # ~20 fps is smoother than the eye needs and costs almost nothing.
        self.set_interval(1 / 20, self.repaint)

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
        self.add(f"**you** — {question}", "user")
        self.buffer = ""
        self.dirty = False
        # The answer widget is created lazily, on the first token, so tool
        # lines that arrive first appear ABOVE the reply rather than below it.
        self.answer = None
        self.run_turn(question)

    @work(thread=True, exclusive=True)
    def run_turn(self, question: str) -> None:
        """Runs OFF the UI thread. Must not touch widgets -- only post messages."""
        worker = get_current_worker()
        config_dict = {"configurable": {"thread_id": self.thread_id}}
        payload = {"messages": [{"role": "user", "content": question}]}

        for event in runner.run_turn(self.agent, payload, config_dict):
            # Cancellation is checked BETWEEN events. If the model is mid-call
            # we cannot interrupt it; we stop at the next chunk instead.
            if worker.is_cancelled:
                return
            match event:
                case runner.Token(text=text):
                    self.post_message(Chunk(text))
                case runner.ToolStart(name=name, args=args):
                    self.post_message(ToolLine(summarize(name, args)))
                case runner.Failed(error=error):
                    self.post_message(Finished(error=error))
                    return
        self.post_message(Finished())

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
        """Show a tool call as its own dim line."""
        self.add(f"`{message.label}`", "tool")

    def on_finished(self, message: Finished) -> None:
        """Flush the last text, then tidy up."""
        self.repaint()  # the timer may not have fired since the final token
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
    if name == "execute":
        return f"run: {args.get('command', '')}"
    path = args.get("file_path") or args.get("path") or ""
    return f"{name}: {path}" if path else name
