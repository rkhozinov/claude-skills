---
name: tuxedo
description: Use when the user wants to add, list, complete, or manage tasks in their tuxedo/todo.txt task list — "add a task", "what's on my todo list", "mark task done", "my tuxedo todos"
---

# tuxedo

## Overview
`tuxedo` is a local CLI/TUI for todo.txt task files (installed via `brew install tuxedo`). No daemon, no API — every command is a one-shot process that reads/writes a plain text file. Use the CLI subcommands (never the TUI) for agent-driven task management.

## Which file it edits
Resolution order: `$TODO_FILE` → `$TODO_DIR/todo.txt` → `./todo.txt`. If the user has a personal task file (e.g. synced via iCloud), set `TODO_FILE` to that path before running commands. Otherwise commands act on `./todo.txt` in the current directory.

## Commands
Task numbers are 1-based **file line numbers**, exactly as printed by `list` — not sorted-view position.

| Action | Command |
|---|---|
| Add | `tuxedo add "TEXT"` — supports natural-language dates ("due next friday"), and inline `+project` `@context` `(A)` priority prefix |
| List (machine-readable) | `tuxedo list --json` or `tuxedo --json list` (either order works) |
| List (human) | `tuxedo list [TERM]` — TERM filters by `+project`, `@context`, or free text |
| Set priority | `tuxedo pri N LETTER` (e.g. `tuxedo pri 1 A`) — cannot be combined into `add` except via inline `(A)` prefix in the text |
| Complete | `tuxedo do N` (aliases: `done`, `complete`) |
| Delete | `tuxedo del N -f` (`-f` skips the confirmation prompt; without it, prompts interactively — always pass `-f` in scripted/agent use) |
| Archive done tasks | `tuxedo archive` — moves completed tasks to `done.txt` |
| List projects/contexts | `tuxedo listproj`, `tuxedo listcon` |

Full list: `tuxedo --help`.

## JSON shape
`tuxedo list --json` returns an array of `{n, raw, done, priority, created, completed, projects, contexts, due, rec, t}`. Use `n` for subsequent `do`/`pri`/`del` calls.

## Common mistakes
- Don't use `-d`/config-file flags — todo.txt-cli's `-d` doesn't exist here; use `TODO_DIR`/`TODO_FILE` env vars instead.
- `do` does **not** auto-archive — completed tasks stay in the file until `tuxedo archive`.
- `del` prompts interactively unless `-f` is passed — always pass `-f` when scripting.
