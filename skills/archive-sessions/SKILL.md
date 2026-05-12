---
name: archive-sessions
description: >
  Archive stale Claude Code session transcripts (default >30 days) into per-project
  monthly tar.gz archives under ~/.claude/archive/. Removes orphan todo files for
  archived sessions. Skips transcripts of live claude processes. Dry-run preview
  with confirm before any deletion. Trigger: /archive-sessions [days] or
  "archive old claude sessions".
---

# Archive Sessions

## Purpose

Reclaim disk under `~/.claude/projects/`. Old `.jsonl` transcripts accumulate forever — each session adds one. This skill compresses transcripts older than N days into per-project monthly tarballs and deletes orphan todo files. Live session transcripts are detected via `lsof` and never touched.

## Trigger

`/archive-sessions [days]` or "archive old claude sessions"

Default age threshold: 30 days.

## Process

1. The script lives in `archive-sessions/scripts/` adjacent to this `SKILL.md`. If path not obvious, search for `archive-sessions/scripts/__main__.py`.

2. Run:

```
cd ~/.claude/skills/archive-sessions && python3 -m scripts [--days N] [--yes]
```

3. The CLI will:
   - detect live `claude` PIDs and exclude their open `.jsonl` files
   - find candidates older than `--days` (default 30)
   - group by project + YYYY-MM
   - print dry-run plan: file count, MB, target archive paths
   - prompt `Y/n` (skip with `--yes`)
   - tar+gzip each group to `~/.claude/archive/YYYY-MM/<project>.tar.gz`
   - verify archive contents match input, then delete sources
   - delete orphan `~/.claude/todos/<uuid>-*.json` for archived session UUIDs
   - print bytes freed and archive paths

4. Restore single archive:

```
python3 -m scripts --restore ~/.claude/archive/2025-11/<project>.tar.gz
```

## Safety

- Live PID detection via `lsof -p <claude_pid>` — current session's transcript never archived
- Archive verified (`tar -tzf` count matches input) before any deletion
- Idempotent: re-running archives 0 new files
- Orphan todo deletion only for UUIDs successfully archived in this run

## Args

| Flag | Default | Meaning |
|---|---|---|
| `--days N` | 30 | Age threshold in days |
| `--yes` | off | Skip Y/n confirmation |
| `--dry-run` | off | Preview only, no writes |
| `--restore PATH` | — | Extract archive back into `~/.claude/projects/<slug>/` |

## Layout

```
~/.claude/skills/archive-sessions/
├── SKILL.md
└── scripts/
    ├── __init__.py
    ├── __main__.py        # entrypoint
    ├── archive.py         # core
    └── live_sessions.py   # PID + lsof
```
