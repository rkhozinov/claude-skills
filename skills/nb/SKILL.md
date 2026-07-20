---
name: nb
description: Use when the user wants to capture, find, or manage notes in their nb notebook — "note that", "write that up", "make a note", "what did I note about X", "my notes", "check nb". Also use proactively when a session produces a durable finding worth keeping (see the bar below). NOT for tasks (→ tuxedo) and NOT for Claude's own session memory (→ /remember).
---

# nb

## Overview
`nb` is a local CLI for plain-markdown notes (`brew install nb`). No daemon, no API — every command is a one-shot process that reads/writes `.md` files in a directory. Use the CLI subcommands; never `nb browse` (local web UI) in agent context.

## Where notes live
`nb_dir` is written to `~/.nbrc` as `export NB_DIR="${NB_DIR:-<path>}"`, and **nb sources that file itself**. Unlike `tuxedo`, there is no profile-env problem — a non-interactive agent shell resolves the right notebook with no `export` of its own. Do not cargo-cult tuxedo's `export TODO_FILE` dance; it has no nb equivalent.

Note the `${NB_DIR:-...}` default-assignment: an `NB_DIR` **already present in the environment silently wins** over `~/.nbrc`. So never set `NB_DIR` for a one-off command unless you mean to redirect every nb call in that shell.

Check where you're writing before a write: `nb settings get nb_dir` and `nb notebooks current`.

Current setup: notebook lives inside the Obsidian iCloud container, so notes sync to the user's phone and are readable/editable in Obsidian iOS. Details are in the user's own `icloud-obsidian-setup` note (`nb show icloud-obsidian-setup`) — don't duplicate them here.

## Routing: nb vs /remember vs tuxedo
Three stores, three jobs. Ask **who reads it, and when**:

| Who reads it | Goes to | Why |
|---|---|---|
| Claude, next session | `/remember` | session-scoped, SQLite, Claude-facing |
| The user, in six months | **nb** | durable, human-facing, syncs to their phone |
| Either — but it needs *doing* | `tuxedo` | actionable, has a next step |

**nb has its own todo type (`nb todo add`, `nb todos`, `nb do`). Do not use it.** tuxedo owns tasks — it has priorities, projects, contexts, natural-language dates and `--json`. Two todo lists means the phone shows only one of them. If a note surfaces an action, add it to tuxedo and reference it from the note.

## When to write a note unprompted
Write proactively only when **all three** hold:

1. A future user would search for it
2. It is not already recoverable from `git log`, a PR body, or Linear
3. It cost real effort to discover

**Clears the bar:** "nb git-inits any directory inside `nb_dir` without asking, so pointing `nb_dir` at an existing vault silently commits it" — non-obvious, expensive to rediscover, written nowhere else.

**Does not clear the bar:** routine edits; "bumped image tag to X" (git has it); anything already written into a PR body; anything that is really a task; anything `/remember` covers.

When in doubt, ask — one line, not a menu. Bloating the vault is worse than missing a note, because notes have no `archive` escape hatch the way todo.txt does.

## Claude-authored notes: breadcrumbs
Append a footer so every Claude-written note traces back to its origin. Same convention as the tuxedo skill, and `nb search cc:` finds them all.

nb always writes `# <title>` as line 1, so **YAML frontmatter is impossible via `nb add`** — injected `---` lands on line 3 and Obsidian renders it as a horizontal rule, not Properties. Use a footer block:

```
cc:<session-uuid>
dir:<absolute-path>
repo:<url>
ref:<pointer>
```

Values are a **single token — no spaces**. Human context goes in the note body; structured pointers go in the footer.

- `cc:` — **always add this, and use the RESUMABLE id** so the user can `claude --resume <id>` to reopen the session the note came from. That id is the session **UUID**, not the `session_…` string from any `Claude-Session` URL. **Never fabricate it** — look it up and verify:
  ```bash
  ls -t ~/.claude/projects/<cwd-slug>/*.jsonl | head -1   # basename minus .jsonl = session id
  grep -l "<unique string from this conversation>" ~/.claude/projects/<cwd-slug>/<id>.jsonl
  ```
- `dir:` — where the work lives on disk. `repo:` — git remote (omit until pushed). `ref:` — any other pointer (`ref:<prefix>-123`).

## Commands
Note IDs are the numbers printed by `nb list`. **Deleted IDs are never recycled** — a fresh notebook can start at `[5]`.

| Action | Command |
|---|---|
| Add | `nb add --title "T" --tags a,b --content "..." < /dev/null` |
| List | `nb list --no-color` |
| Search | `nb search <term> --no-color` (ripgrep under the hood; searches the footer too) |
| Show / edit / delete | `nb show N`, `nb edit N`, `nb delete N --force` |
| By title | any command takes a title instead of N: `nb show icloud-obsidian-setup` |
| Tags | `--tags a,b` on add; nb writes them as inline `#a #b` under the H1 |
| Git history | `nb git log --oneline` — nb auto-commits every write |

Full reference: `nb help`, `nb help <subcommand>`.

## Agent gotchas
Each of these cost a real retry. All verified.

- **`nb add` hangs forever without a TTY.** Always redirect: `nb add ... < /dev/null`. This is the big one — it burns the full command timeout with no output.
- **ANSI colour is emitted even when piped, and `NO_COLOR=1` is ignored.** Pass `--no-color` on anything you intend to parse.
- **There is no `--json`.** Unlike tuxedo. Output is line-based `[N] title` — parse that, don't go looking for a structured flag.
- **nb adopts any directory inside `nb_dir` as a notebook and `git init`s it, unprompted.** Never point `nb_dir` at a directory holding anything you don't want committed.
- **`nb git log` is git** — newest first. `| tail` shows the *oldest* commits; use `| head`.
- Notes are plain `.md` and are the source of truth. If `.git` inside a notebook ever breaks (iCloud eviction can do this), deleting it loses history but no notes.

## Common mistakes
- Using `nb todo add` — tasks belong in tuxedo (see Routing).
- Writing a note for something already captured in a PR body or `git log`.
- Parsing `nb list` without `--no-color`, then matching against invisible escape codes.
- Assuming a fresh notebook starts at `[1]`.
