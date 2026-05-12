---
name: linear
description: Everyday Linear issue ops — create, list, comment, get, update, start/stop/close, assign. Use this for typical work like "create an issue", "comment on <prefix>-123", "what are my open issues". For projects, cycles, bulk operations, team transfers, attachments, advanced filters/templates, use the `linear-power` skill instead.
user_invocable: false
---

# Linear CLI — Everyday

Bundled Python uv-script. Auth: `$LINEAR_API_KEY`. Invoke as `${CLAUDE_PLUGIN_ROOT}/skills/linear/bin/linear-cli` (or just `linear-cli` if symlinked into PATH).

## Defaults (env vars)

| Var | Effect |
|-----|--------|
| `LINEAR_API_KEY` | Auth (required) |
| `LINEAR_DEFAULT_TEAM` | Used when `--team` is omitted on `issues create`, `issues list`, `projects create` |
| `LINEAR_DEFAULT_PROJECT` | Used as default `--project` on create/list when omitted |

Set in your shell rc so you stop typing `--team "<team>"` on every command. CLI args still override env.

## Quick reference

| Task | Command |
|------|---------|
| Create issue | `linear-cli issues create "Title" --team "<team>" -p 2` |
| List my issues | `linear-cli i list --mine --limit 10` |
| List team issues | `linear-cli i list --team "<team>" --state "In Progress"` |
| Get issue | `linear-cli i get <prefix>-123` |
| Get with comments | `linear-cli i get <prefix>-123 --comments` |
| Update title/state | `linear-cli i update <prefix>-123 -T "New" -s "Done"` |
| Comment | `linear-cli issues comment <prefix>-123 --body "Text"` |
| Start (in progress + assign me) | `linear-cli i start <prefix>-123` |
| Stop (back to backlog) | `linear-cli i stop <prefix>-123` |
| Close (done) | `linear-cli i close <prefix>-123` |
| Assign | `linear-cli i assign <prefix>-123 me` |
| Whoami | `linear-cli whoami` |
| Labels (preview before use) | `linear-cli labels list --team "<team>"` |

## Create — flags

`linear-cli issues create [OPTIONS] <TITLE>` (title is **positional**, not `--title`).

| Flag | Short | Purpose |
|------|-------|---------|
| `--team` | `-t` | Team **name** (required) — `"<team>"`, not `"<prefix>"` |
| `--description` | `-d` | Markdown body. Use `-` to read from stdin |
| `--priority` | `-p` | 0=none, 1=urgent, 2=high, 3=normal, 4=low |
| `--state` | `-s` | State name (e.g. `"Backlog"`, `"Todo"`) |
| `--assignee` | `-a` | `"me"`, user name, email, or UUID |
| `--labels` | `-l` | Repeat for multiple |
| `--due` | | `today`, `tomorrow`, `+3d`, `+1w`, `YYYY-MM-DD` |
| `--estimate` | `-e` | Points |
| `--dry-run` | | Show payload without creating |

## Update

`linear-cli issues update [OPTIONS] <ID>` (ID positional). Title flag is `-T` (capital), not `--title`.

If `--state "Name"` fails validation: use `--data '{"stateId": "UUID"}'` with the workflow state UUID. Project: `--project "Name"` or `--project none` to clear.

## Output

Default human table. Override:

```bash
--output json       # structured JSON
--output ndjson     # one object per line
--fields "identifier,title,state.name"
--format '{{identifier}} {{title}}'
--id-only           # just identifiers, scripting-friendly
```

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| `--title "X"` on create | Title is positional: `create "X"` |
| `--status "Done"` | Flag is `--state` (or `-s`) |
| `--team "<prefix>"` | Use full name: `"<team>"` |
| `--label "nonexistent"` | Labels must exist; check with `labels list --team "<team>"` |
| `show <prefix>-123` | Subcommand is `get`, not `show` |

## Team name → key

<team>=<prefix>, IT=IT, <team>=<prefix>, <team>=<prefix>, Data=<prefix>, <prefix>=<prefix>, <team>=<prefix>, <team>=<prefix>, <team>=<prefix>, <team>=<prefix>, <org>=<prefix>, <team>=<prefix>, <team>=<prefix>, <team>=<prefix>, <team>=<prefix>.

Use the **name** with `--team`. The key is the issue prefix (`<prefix>-123`).
