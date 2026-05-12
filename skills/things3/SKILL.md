---
name: things3
description: "Read, add, and manage todos in Things 3 on macOS. Use when user wants to list/search Things todos, send tasks to Things 3, or create Things projects."
argument-hint: "[todo text, 'list today', 'search QUERY', or 'from file <path>']"
allowed-tools: Bash, Read
---

# Things 3 Skill

Read and write todos in Things 3 on macOS. Use the helper script at `~/.claude/skills/things3/things3.py` for all operations.

## Read Commands (SQLite)

### List Todos

```bash
python3 ~/.claude/skills/things3/things3.py list today
python3 ~/.claude/skills/things3/things3.py list inbox 20
```

Available lists: `today`, `inbox`, `upcoming`, `anytime`, `someday`, `logbook`, `projects`, `trash`. Optional second arg is limit (default 50).

### Search Todos

```bash
python3 ~/.claude/skills/things3/things3.py search "keyword"
```

Searches title and notes of all non-trashed todos.

## Write Commands (URL scheme)

### Single Todo

```bash
python3 ~/.claude/skills/things3/things3.py add --title="Buy milk" --when=today --tags=Errands
```

**Parameters:** `--title` (required), `--notes`, `--when`, `--deadline`, `--tags` (comma-separated), `--list`, `--heading`, `--checklist-items` (newline-separated with `%0a`), `--completed=true`.

**`when` values:** `today`, `tomorrow`, `evening`, `anytime`, `someday`, or `yyyy-mm-dd`. **`deadline`:** `yyyy-mm-dd` only.

### Batch Todos (JSON)

```bash
python3 ~/.claude/skills/things3/things3.py json '[
  {"type":"to-do","attributes":{"title":"Buy milk","when":"today","tags":["Errands"]}},
  {"type":"to-do","attributes":{"title":"Call dentist","when":"tomorrow"}}
]'
```

### Project with Todos

```bash
python3 ~/.claude/skills/things3/things3.py json '[{
  "type":"project",
  "attributes":{
    "title":"Website Redesign","when":"today","tags":["Work"],
    "items":[
      {"type":"to-do","attributes":{"title":"Create wireframes","when":"today"}},
      {"type":"heading","attributes":{"title":"Development"}},
      {"type":"to-do","attributes":{"title":"Build frontend"}}
    ]
  }
}]'
```

### Show a List (opens Things 3 UI)

```bash
python3 ~/.claude/skills/things3/things3.py show today
```

## Modify Commands (AppleScript)

### Move Todos Between Lists

```bash
python3 ~/.claude/skills/things3/things3.py move Today Inbox
python3 ~/.claude/skills/things3/things3.py move Inbox Someday
```

Moves all todos from SOURCE list to DEST list. Uses AppleScript (loops internally to avoid bulk failures). Note: todos belonging to projects/areas may not move.

### Delete Todos

```bash
python3 ~/.claude/skills/things3/things3.py delete Inbox
python3 ~/.claude/skills/things3/things3.py delete Today "WNMS"
```

Deletes all todos from a list, or only those matching a title substring filter.

## Rules

1. **Tags must already exist** in Things 3 — the URL scheme cannot create new tags.
2. **Rate limit**: max 250 items per JSON call, max one call per 10 seconds.
3. For >50 todos, split into multiple JSON calls.
4. **Always use the helper script** — never construct `things:///` URLs manually in bash.
5. **Read is read-only** — the SQLite database must never be written to directly.

## Intent Mapping

- "Show my today" / "what's on my list" / "list todos" → `list`
- "Find" / "search" → `search`
- Single task / "remind me to" → `add`
- List of todos / extract from transcript → `json` with array
- Structured project with phases → `json` with project type
- "Open inbox" (in Things UI) → `show`
- "Move today to inbox" / "move all" → `move`
- "Delete" / "remove todos" → `delete` (with optional title filter)
- From a file: read file first, extract actionable items, then batch via `json`.
