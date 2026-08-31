#!/usr/bin/env python3
"""Counting subagent for data/*.txt files"""

import subprocess
import sys


def delegate_to_subagent(cmd):
    """Delegates a task to a subagent via system shell execution."""
    if cmd:
        # Execute the delegated command through shell
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    else:
        print("No command provided", file=sys.stderr)
        sys.exit(1)


def count_txt_files():
    """Delegate counting all lines in data/*.txt files to subagent."""
    # Delegates to the system's shell command executor for this task
    delegate_to_subagent('find data -name "*.txt" | wc -l')


if __name__ == "__main__":
    count_txt_files()
