"""
DeepCoder - Entry Point
=======================
- Builds the app and hands the terminal to Textual
- The interesting code lives in tui.py (the UI) and runner.py (the events)

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
