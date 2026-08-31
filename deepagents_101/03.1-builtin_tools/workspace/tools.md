# DeepAgents Built‑in Tools

These are the tools you can call directly from the DeepAgents environment. Each entry includes a short description of its purpose and typical usage.

---

## `ls`
**Description:** Lists all files and directories in a given path. Useful for exploring the filesystem and confirming that a directory exists before performing other operations.
**Parameters:**
- `path` (required, absolute): The directory to list. Must be an absolute path.

---

## `read_file`
**Description:** Reads a file from the filesystem. Returns up to 100 lines by default, starting from the beginning. For larger files you can specify `offset` and `limit` to page through the content.
**Parameters:**
- `file_path` (required, absolute): Path to the file to read.
- Optional `limit` (int): Maximum number of lines to read (default 100).
- Optional `offset` (int): Line number to start reading from (0‑indexed, default 0).

---

## `write_file`
**Description:** Writes content to a file. Creates the file if it does not exist or overwrites it if it does.
**Parameters:**
- `file_path` (required, absolute): Path where the file should be written.
- `content` (required): The text content to write.

---

## `edit_file`
**Description:** Performs exact string replacements in an existing file. Reads the file first, then replaces occurrences of `old_string` with `new_string`. If `replace_all` is true, all occurrences are replaced; otherwise only the first match.
**Parameters:**
- `file_path` (required, absolute): Path to the file to edit.
- `old_string` (required): Text to find and replace.
- `new_string` (required): Text to insert in place of `old_string`.
- Optional `replace_all` (bool): Whether to replace all occurrences (default false).

---

## `delete`
**Description:** Permanently deletes a file or directory from the filesystem. Deleting a directory removes it recursively.
**Parameters:**
- `file_path` (required, absolute): Path of the file or directory to delete.

---

## `glob`
**Description:** Finds files matching a glob pattern. Useful for locating specific files without knowing their exact names.
**Parameters:**
- `pattern` (required): Glob pattern (e.g., `*.txt`, `data/**/*.md`).
- Optional `path` (string): Base directory to start the search (default current working directory).

---

## `grep`
**Description:** Searches for a literal text pattern across files. The pattern is matched verbatim (not regex). Returns matching file paths or content based on `output_mode`.
**Parameters:**
- `pattern` (required): Text to search for.
- Optional `glob` (string): Limit search to specific file extensions or types.
- Optional `max_count` (int): Cap on total matches returned.
- Optional `output_mode` (enum): `files_with_matches`, `content`, or `count`.
- Optional `path` (string): Directory to search (default current working directory).

---

## `execute`
**Description:** Executes a shell command in an isolated sandbox and returns the combined stdout/stderr with the exit code. Use this for any shell operation that isn’t covered by the other tools.
**Parameters:**
- `command` (required): The shell command to run.
- Optional `timeout` (int): Seconds to allow the command to run before timing out.

---

## `write_todos`
**Description:** Manages a structured task list for the current work session. Use it to track progress on multi‑step tasks, mark tasks as pending, in‑progress, or completed, and update the list as you finish steps.
**Parameters:**
- `todos` (required): An array of todo objects, each with `content` (string) and `status` (`pending`, `in_progress`, or `completed`).

---

*These tools give you full filesystem manipulation, text editing, and programmatic searching capabilities within the DeepAgents environment.*