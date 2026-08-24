"""
Slash commands: things the USER does, not the model.
====================================================
Anything starting with "/" is handled here and never reaches the agent.
Each command is a plain method; the registry is built by introspection, so
adding a command is: write one method, done.
"""

import uuid


class Commands:
    """The /command registry. The app passes itself in so commands can act."""

    def __init__(self, app) -> None:
        self.app = app

    # %% The commands. Docstrings double as /help text.
    def cmd_help(self) -> str:
        """List every command."""
        lines = ["**commands**", ""]
        for name, method in sorted(self.entries().items()):
            lines.append(f"- `/{name}` — {method.__doc__.strip()}")
        return "\n".join(lines)

    def cmd_new(self) -> str:
        """Start a fresh conversation (new thread, clean allowlist)."""
        self.app.thread_id = uuid.uuid4().hex[:8]
        self.app.allowlist.clear()
        return f"new conversation — thread `{self.app.thread_id}`"

    def cmd_clear(self) -> str:
        """Clear the chat log on screen (the conversation itself continues)."""
        self.app.query_one("#chat").remove_children()
        return ""

    def cmd_model(self, name: str = "") -> str:
        """Show the model, or switch: /model ollama:qwen3.5:4b."""
        import config
        from agent import build_agent

        if not name:
            return f"model: `{config.MODEL}`  — switch with `/model provider:model`"
        config.MODEL = name
        self.app.agent = build_agent()  # rebuild with the new model
        return f"switched to `{name}` (new agent, same thread)"

    def cmd_init(self) -> str:
        """Explore the project and write AGENTS.md (the agent's standing rules)."""
        self.app.send(
            "Explore this project with ls, glob and read_file, then write /AGENTS.md: "
            "a short guide for coding agents. Sections: What this project is, Layout, "
            "Conventions, Commands (build/test/run). Under 40 lines. "
            "If AGENTS.md already exists, improve it instead of starting over."
        )
        return ""

    def cmd_resume(self) -> str:
        """Pick an earlier conversation and continue it."""
        self.app.pick_thread()
        return ""

    def cmd_quit(self) -> str:
        """Leave DeepCoder."""
        self.app.exit()
        return ""

    # %% Dispatch
    def entries(self) -> dict:
        """name -> bound method, discovered from the cmd_ prefix."""
        return {
            name.removeprefix("cmd_"): getattr(self, name)
            for name in dir(self)
            if name.startswith("cmd_")
        }

    def run(self, line: str) -> str | None:
        """Execute a /command line. Returns display text, or None if unknown."""
        name, _, argument = line.lstrip("/").partition(" ")
        method = self.entries().get(name)
        if method is None:
            return f"unknown command `/{name}` — try `/help`"
        try:
            return method(argument.strip()) if argument.strip() else method()
        except TypeError:
            return f"`/{name}` does not take arguments"

    def names(self) -> list[str]:
        """Completion candidates for the input's suggester."""
        return [f"/{name}" for name in self.entries()]
