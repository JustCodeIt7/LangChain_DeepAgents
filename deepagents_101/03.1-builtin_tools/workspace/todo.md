# Built-in Tools in DeepAgents

## ls
Lists all files in a directory.

This is useful for exploring the filesystem and finding the right file to read or edit.

## read_file
Reads a file from the filesystem.

Usage: by default reads up to 100 lines starting from the beginning of the file. Use `offset`/`limit` to page through large files instead of reading them whole.

## write_file
Writes content to a file. Creates the file if it does not exist; replaces it entirely if it does.

Usage: use this tool when you intend to create a new file or replace the whole file. You do not need to read the file first.

## edit_file
Performs exact string replacements in files.

Usage: you must read the file before editing; preserve the exact indentation from the read output, and never include line-number prefixes in old_string or new_string. Prefer editing an existing file over creating a new one.

## delete
Deletes a file or directory from the filesystem.

Usage: permanently removes the file or directory at the given absolute path.

## glob
Find files matching a glob pattern, returning absolute paths.

Supports `*` (any characters within a path segment), `**` (any directories), `?` (single character), `[abc]` (one character from a set), and `{a,b}` (alternatives), e.g. `*.py`, `**/*.py`, `*.{yml,yaml}`.

## grep
Search for a LITERAL text pattern across files (NOT regex).

The pattern is matched verbatim: regex metacharacters are ordinary characters, not operators. To match any of several strings, run a separate grep for each; `grep(pattern="foo|bar")` searches for the literal text "foo|bar", and `.*` or `\.` match those characters literally.

## execute
Executes a shell command in an isolated sandbox and returns combined stdout/stderr with the exit code (truncated if very large).

Usage: quote paths containing spaces (e.g. cd "/path/with spaces").

Chain commands with ';' or '&&' (use '&&' when a command depends on the previous); do not use newlines except inside quoted strings.

Only available on backends implementing SandboxBackendProtocol; otherwise it returns an error.

## task
Launch an ephemeral subagent to handle a complex, multi-step task in an isolated context window.

Available agent types and the tools they have access to:
- general-purpose: General-purpose agent for researching complex questions, searching for files and content, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. This agent has access to all tools as the main agent.

Specify subagent_type to select the agent. Usage notes:
- Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls.
- Each invocation is stateless: the agent sees only the prompt you give it and returns a single final report. Put full detail in the prompt and state exactly what it should return.
- The agent's report is not shown to the user; relay a summary yourself.
- Tell the agent whether to create content, analyze, or only research, since it cannot see the user's intent.
- If an agent's description says to use it proactively, do so without waiting to be asked.
- When only general-purpose is available, use it for any complex, context-heavy task; it has the same capabilities as the main agent.