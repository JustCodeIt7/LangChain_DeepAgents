# Built-in Tools in DeepAgents

These are the tools currently available for use within the DeepAgents environment, along with brief descriptions of each.

---

## 1. **ls**
**Description:** Lists all files in a specified directory. Useful for exploring the filesystem and locating the correct file to read or edit. Always use this tool before using `read_file` or `edit_file` to ensure you are targeting the right file.

---

## 2. **read_file**
**Description:** Reads a file from the filesystem. For text files, it defaults to reading the first 100 lines starting from the beginning. You can page through large files using `offset` and `limit` parameters. Returns line numbers prefixed for text files.

---

## 3. **write_file**
**Description:** Writes content to a file. Creates the file if it does not exist; replaces it entirely if it does. Prefer editing an existing file over creating a new one when possible.

---

## 4. **edit_file**
**Description:** Performs exact string replacements in files. You must read the file first; this tool errors otherwise. Preserve exact indentation and do not include line-number prefixes in `new_string` unless `replace_all` is true.

---

## 5. **delete**
**Description:** Deletes a file or directory from the filesystem. Permanently removes the target; cannot be undone. Use only for paths you are sure are no longer needed.

---

## 6. **glob**
**Description:** Finds files matching a glob pattern, returning absolute paths. Supports `*`, `**`, `?`, and bracket notation (`[abc]`). A leading `/` anchors the search to the root directory.

---

## 7. **grep**
**Description:** Searches for a literal text pattern across files (not regex). Returns matching files or content based on `output_mode`. Useful for locating specific text without using regex.

---

## 8. **execute**
**Description:** Executes a shell command in an isolated sandbox and returns combined stdout/stderr with the exit code. Use for complex shell operations; avoid using `find` or `grep` directly; prefer the provided `grep` and `glob` tools.

---

## 9. **write_todos**
**Description:** Use this tool to create and manage a structured task list for the current work session. Helps track progress and organize complex tasks. Only use when the task is multi‑step, non‑trivial, or requires careful planning.

---

*This markdown file serves as a quick reference to the available tools and their purposes.*