---
name: tuxedo
description: Use when the user wants to add, list, complete, or manage tasks in their tuxedo/todo.txt task list — "add a task", "what's on my todo list", "mark task done", "my tuxedo todos"
---

# tuxedo

## Overview
`tuxedo` is a local CLI/TUI for todo.txt task files (installed via `brew install tuxedo`). No daemon, no API — every command is a one-shot process that reads/writes a plain text file. Use the CLI subcommands (never the TUI) for agent-driven task management.

## Which file it edits
Resolution order: `$TODO_FILE` → `$TODO_DIR/todo.txt` → `./todo.txt`. If the user has a personal task file (e.g. synced via iCloud), set `TODO_FILE` to that path before running commands. Otherwise commands act on `./todo.txt` in the current directory.

**Agent gotcha — always target the GLOBAL file.** The user exports `TODO_FILE` in their shell profile, but the non-interactive shell an agent runs in does NOT load that profile — `TODO_FILE` comes back unset and tuxedo silently falls to `./todo.txt` in the cwd (wrong file, e.g. inside some unrelated repo). So **resolve and `export TODO_FILE` explicitly in every command block**:
```bash
grep -h 'TODO_FILE' ~/.zshrc ~/.zprofile ~/.zshenv 2>/dev/null   # e.g. "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Tuxedo/todo.txt"
export TODO_FILE="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Tuxedo/todo.txt"
```
If no `TODO_FILE` is configured anywhere, ask the user for their global path — never default to `./todo.txt`.

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

## Claude-authored tasks (metadata breadcrumbs)
When **you (Claude) add a task on the user's behalf**, append `key:value` metadata so every task traces back to its origin — todo.txt has no notes field, so these tags are how context survives:

- `cc:<session-id>` — **always add this, and use the RESUMABLE id** so the user can `claude --resume <id>` to reopen the exact session the task came from. That id is the session **UUID**, not the `session_…` string from any `Claude-Session` URL (that URL may be absent, and its id is not what `--resume` takes). **Never fabricate it** — look it up and verify:
  ```bash
  # UUID = the agent scratchpad dir's basename, and the newest transcript for this cwd:
  ls -t ~/.claude/projects/<cwd-slug>/*.jsonl | head -1     # basename minus .jsonl = session id
  grep -l "<a unique string from this conversation>" ~/.claude/projects/<cwd-slug>/<id>.jsonl   # confirm it's really this session
  ```
- `dir:<absolute-path>` — where the work lives on disk (so a future session can `cd` straight there). Single token, no spaces.
- `repo:<url>` — git remote / GitHub URL. Omit (or `repo:local`) until the repo is pushed.
- `pr:<url>` — the PR, once one is opened.
- `ref:<pointer>` — any other origin breadcrumb (`ref:PROJ-123`) pointing at where detail lives.

`key:value` values are a **single token — no spaces**. Put human context in the task text, structured pointers in tags. Always `export TODO_FILE` first (see the gotcha above):

```bash
export TODO_FILE="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Tuxedo/todo.txt"
tuxedo add "add retry logic to the upload path +api-client @feature \
  dir:/Users/me/repos/api-client cc:613bb074-6d6c-4de1-923f-7cc98ba3a203"
```

Review Claude-created tasks: `tuxedo list "cc:"` (matches any session) or filter by a specific `cc:` id / `dir:` path.

## JSON shape
`tuxedo list --json` returns an array of `{n, raw, done, priority, created, completed, projects, contexts, due, rec, t}`. Use `n` for subsequent `do`/`pri`/`del` calls.

## Common mistakes
- Don't use `-d`/config-file flags — todo.txt-cli's `-d` doesn't exist here; use `TODO_DIR`/`TODO_FILE` env vars instead.
- `do` does **not** auto-archive — completed tasks stay in the file until `tuxedo archive`.
- `del` prompts interactively unless `-f` is passed — always pass `-f` when scripting.
