"""
The Textual app shell.
======================
A chat log you can scroll, an input you can type in, and a status line.

This version calls the agent DIRECTLY from the submit handler, which freezes
the whole UI until the answer arrives. That is deliberate: Part 9 fixes it
with a worker, and the fix means much more once you have felt the freeze.
"""

import config
import runner
from agent import build_agent
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Input, Markdown, Static


class DeepCoderApp(App):
    """The DeepCoder terminal UI."""

    CSS_PATH = "app.tcss"
    TITLE = "DeepCoder"

    def __init__(self, agent=None, thread_id: str = "tui") -> None:
        super().__init__()
        # Accepting an agent makes the app testable: a stub agent means the
        # UI can be exercised without a model running anywhere.
        self.agent = agent if agent is not None else build_agent()
        self.thread_id = thread_id

    # %% Step 1: Lay out the screen
    def compose(self) -> ComposeResult:
        """Build the widget tree, top to bottom."""
        yield Header()
        yield VerticalScroll(id="chat")
        yield Input(placeholder="Ask DeepCoder…  (ctrl+c to quit)", id="prompt")
        yield Static(config.describe(), id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the input so you can type immediately."""
        self.query_one("#prompt", Input).focus()

    # %% Step 2: Add a line to the chat log
    def say(self, markdown: str, css_class: str) -> None:
        """Append a message to the chat log and scroll to it."""
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Markdown(markdown, classes=css_class))
        chat.scroll_end(animate=False)

    # %% Step 3: Handle a submitted question
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Run the agent when the user presses Enter.

        THE PROBLEM: this runs on the UI thread. Textual cannot redraw, scroll
        or even show your keystrokes until run_turn() finishes, so the app
        looks hung for the entire answer. Part 9 moves this into a worker.
        """
        question = event.value.strip()
        if not question:
            return
        event.input.value = ""
        self.say(f"**you** — {question}", "user")

        config_dict = {"configurable": {"thread_id": self.thread_id}}
        payload = {"messages": [{"role": "user", "content": question}]}
        answer: list[str] = []

        # Blocking loop. Collect the whole answer, then render it at the end.
        for chunk in runner.run_turn(self.agent, payload, config_dict):
            match chunk:
                case runner.Token(text=text):
                    answer.append(text)
                case runner.ToolStart(name=name):
                    answer.append(f"\n\n`{name}`\n\n")
                case runner.Failed(error=error):
                    answer.append(f"\n\n**error:** {error}")

        self.say("".join(answer).strip() or "_(no answer)_", "assistant")
