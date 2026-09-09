"""
DeepCoder 08 - A Real Terminal UI
=================================
- Textual gives us a chat log, an input box and a status line
- The agent is called straight from the submit handler, so the UI FREEZES
- That freeze is the whole lesson; Part 9 fixes it with a worker

Run:  python main.py
"""

# %% Step 1: Imports and setup
import uuid

from tui import DeepCoderApp


# %% Step 2: Start the app
def main() -> None:
    """Build the app and hand control to Textual."""
    # App.run() takes over the terminal (alternate screen, mouse, key capture)
    # and does not return until the user quits with ctrl+c.
    DeepCoderApp(thread_id=uuid.uuid4().hex[:8]).run()


if __name__ == "__main__":
    main()
