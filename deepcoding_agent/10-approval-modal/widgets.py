"""
The approval dialog.
====================
One modal per pause. It lists EVERY pending action, because a single pause
can carry several tool calls, and returns one decision per action in order.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


def summarize(action: dict) -> str:
    """One readable line describing what the agent wants to do."""
    name = action.get("name", "?")
    args = action.get("args", {}) or {}
    if name == "execute":
        return f"$ {args.get('command', '')}"
    path = args.get("file_path") or args.get("path") or ""
    return f"{name}  {path}" if path else f"{name}({args})"


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
