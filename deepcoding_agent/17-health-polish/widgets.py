"""
The approval dialog.
====================
One modal per pause. It lists EVERY pending action, because a single pause
can carry several tool calls, and returns one decision per action in order.
"""

import difflib

import config
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, OptionList, Static


def summarize(action: dict) -> str:
    """One readable line describing what the agent wants to do."""
    name = action.get("name", "?")
    args = action.get("args", {}) or {}
    if name == "execute":
        return f"$ {args.get('command', '')}"
    path = args.get("file_path") or args.get("path") or ""
    return f"{name}  {path}" if path else f"{name}({args})"


def _current_text(file_path: str) -> str:
    """What the file on disk says right now ("" if it does not exist yet).

    File tools use virtual paths rooted at "/", and the default backend roots
    them at WORKDIR -- so the real location is WORKDIR / path-without-slash.
    """
    real = config.WORKDIR / file_path.lstrip("/")
    try:
        return real.read_text()
    except (FileNotFoundError, UnicodeDecodeError, OSError):
        return ""


def diff_for(action: dict) -> str | None:
    """A unified diff of what this action would do to the file, or None.

    Only write_file and edit_file change file contents, so only they get a
    diff. We compute the AFTER text the same way the tool will:
      write_file  -> replaces the whole file with `content`
      edit_file   -> replaces old_string with new_string (once, or all)
    """
    name, args = action.get("name"), action.get("args", {}) or {}
    if name not in ("write_file", "edit_file"):
        return None
    path = args.get("file_path", "")
    before = _current_text(path)
    if name == "write_file":
        after = args.get("content", "")
    else:
        count = -1 if args.get("replace_all") else 1
        after = before.replace(args.get("old_string", ""), args.get("new_string", ""), count)
    lines = difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile=f"a{path}", tofile=f"b{path}", lineterm="",
    )
    return "\n".join(lines)


class ApprovalScreen(ModalScreen[list[dict]]):
    """Asks the human about a batch of pending tool calls.

    ModalScreen[list[dict]] means "this screen returns a list of dicts" --
    the decisions, which the waiting worker then feeds back to the graph.
    """

    BINDINGS = [
        ("y", "approve", "Approve"),
        ("n", "reject", "Reject"),
        ("a", "always", "Always"),
        ("escape", "reject", "Reject"),
    ]

    def __init__(self, actions: list[dict]) -> None:
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        """A titled box listing every pending action."""
        count = len(self.actions)
        plural = "action" if count == 1 else "actions"
        with VerticalScroll(id="approval"):
            yield Label(f"DeepCoder wants to run {count} {plural}:", id="approval-title")
            for action in self.actions:
                yield Static(summarize(action), classes="action")
                diff = diff_for(action)
                if diff:
                    # Rich renderables drop straight into a Static; the "diff"
                    # lexer colors +/- lines for free.
                    yield Static(Syntax(diff, "diff", word_wrap=True), classes="diff")
            with Horizontal(id="approval-buttons"):
                yield Button("Approve  (y)", variant="success", id="approve")
                yield Button("Reject  (n)", variant="error", id="reject")
                yield Button("Always  (a)", variant="primary", id="always")

    # %% Decisions: one per action, same order, every time
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Buttons and keys share the same three actions."""
        getattr(self, f"action_{event.button.id}")()

    def action_approve(self) -> None:
        """Run everything in this batch once."""
        self.dismiss([{"type": "approve"} for _ in self.actions])

    def action_reject(self) -> None:
        """Run none of it, and tell the model why."""
        refusal = {"type": "reject", "message": "The user declined this action."}
        self.dismiss([dict(refusal) for _ in self.actions])

    def action_always(self) -> None:
        """Approve, and stop asking about these tool names this session."""
        self.app.allowlist.update(action.get("name", "") for action in self.actions)
        self.dismiss([{"type": "approve"} for _ in self.actions])


class PlanPanel(Static):
    """The agent's todo list, shown beside the chat while it works."""

    MARKS = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]"}

    def show(self, todos: list[dict]) -> None:
        """Redraw the panel from the latest todo list."""
        lines = ["[bold]plan[/bold]"]
        for todo in todos:
            status = todo.get("status", "pending")
            mark = self.MARKS.get(status, "[ ]")
            text = todo.get("content", "")
            style = {"completed": "dim", "in_progress": "bold yellow"}.get(status, "")
            lines.append(f"{mark} [{style}]{text}[/{style}]" if style else f"{mark} {text}")
        self.update("\n".join(lines))
        self.display = bool(todos)


class ResumeScreen(ModalScreen[str | None]):
    """Pick a stored conversation to resume. Returns its thread_id."""

    BINDINGS = [("escape", "dismiss_none", "Cancel")]

    def __init__(self, entries: dict[str, dict]) -> None:
        super().__init__()
        self.entries = entries

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="approval"):  # reuse the dialog styling
            yield Label("Resume a conversation:", id="approval-title")
            options = OptionList(id="threads")
            for thread_id, meta in self.entries.items():
                options.add_option(f"{meta.get('title', '?')}  ({thread_id})")
            yield options

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """The selected row's trailing (thread_id) is the value we need."""
        text = str(event.option.prompt)
        self.dismiss(text.rsplit("(", 1)[-1].rstrip(")"))

    def action_dismiss_none(self) -> None:
        """Escape closes the picker without resuming anything."""
        self.dismiss(None)
