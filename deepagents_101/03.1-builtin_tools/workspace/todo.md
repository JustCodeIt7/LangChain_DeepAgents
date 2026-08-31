# Built-in Tools in Deep Agents

## ls
Lists all files in a directory.

This is useful for exploring the filesystem and finding the right file to read or edit.

## read_file
Reads a file from the filesystem. Assume any path the user provides is valid; reading a missing file returns an error.

Usage:
- For text files, by default it reads up to 100 lines starting from the beginning of the file. Use `offset`/`limit` to page through large files instead of reading them whole.
- Results are returned with line-number prefixes (e.g., `1: text`). Never include these prefixes when editing.
- Lines over 5,000 characters are split with continuation markers (e.g., `5.1`).