---
name: linear-cli
description: Reference skill for Linear operations using linear-cli instead of MCP plugin. Covers issues, projects, cycles, comments, teams, users, and status updates.
user_invocable: false
---

# Linear CLI (`linear-cli`) Reference

Use `linear-cli` for all Linear operations. Do NOT use the Linear MCP plugin tools.

## Authentication

Uses `$LINEAR_API_KEY` environment variable automatically. No separate auth step needed.

## Issues

### Subcommands

| Subcommand | Alias | Description |
|------------|-------|-------------|
| `issues list` | `i list` | List issues |
| `issues get` | `i get` | Get issue details |
| `issues create` | `i create` | Create a new issue |
| `issues update` | `i update` | Update an existing issue |
| `issues delete` | `i delete` | Delete an issue |
| `issues start` | `i start` | Set to In Progress + assign to me |
| `issues stop` | `i stop` | Return to backlog state |
| `issues close` | `i close` | Mark as Done |
| `issues comment` | `i comment` | Add a comment |
| `issues assign` | `i assign` | Assign to a user |
| `issues move` | `i move` | Move to a different project |
| `issues transfer` | `i transfer` | Transfer to a different team |
| `issues open` | `i open` | Open in browser |
| `issues link` | `i link` | Print the issue URL |

### Create

**Syntax**: `linear-cli issues create [OPTIONS] <TITLE>`

Title is a **positional argument** — NOT `--title`.

| Flag | Short | Description | Example |
|------|-------|-------------|---------|
| `--team` | `-t` | Team name (required) | `--team "<team>"` |
| `--description` | `-d` | Markdown description | `-d "Bug details"` |
| `--priority` | `-p` | 0=none, 1=urgent, 2=high, 3=normal, 4=low | `-p 2` |
| `--state` | `-s` | State name | `-s "Backlog"` |
| `--assignee` | `-a` | User ID, name, email, or "me" | `-a "me"` |
| `--labels` | `-l` | Labels (repeatable) | `-l "bug" -l "infra"` |
| `--due` | | Due date | `--due "+3d"`, `--due "tomorrow"`, `--due "2026-04-01"` |
| `--estimate` | `-e` | Points | `-e 3` |
| `--data` | | Raw JSON fields | `--data '{"field":"value"}'` |

```bash
# Basic
linear-cli i create "Fix bug" --team "<team>" --priority 2

# With description, assignee, due date
linear-cli i create "Feature request" --team "<team>" -a "me" --due "+1w" -p 3 \
  --description "Short description here"

# Long markdown description via heredoc
linear-cli i create "Migration plan" --team "<team>" --priority 4 --state "Backlog" \
  --description "$(cat <<'EOF'
## Context
Markdown description here.

## Acceptance Criteria
- [ ] Item one
- [ ] Item two
EOF
)"

# Read description from stdin
linear-cli i create "Task" --team "<team>" --description - <<< "Body from stdin"
```

### List

**Syntax**: `linear-cli issues list [OPTIONS]`

| Flag | Short | Description |
|------|-------|-------------|
| `--team` | `-t` | Filter by team name |
| `--state` | `-s` | Filter by state name |
| `--assignee` | `-a` | Filter by assignee |
| `--mine` | | Shortcut for `--assignee me` |
| `--project` | | Filter by project name |
| `--label` | `-l` | Filter by label name |
| `--since` | | Created after date (`today`, `-7d`, `2024-01-15`) |
| `--group-by` | | Group by `state`, `priority`, or `assignee` |
| `--count-only` | | Show only count of matching issues |
| `--limit` | | Max results |

```bash
linear-cli i list --team "<team>" --state "In Progress"
linear-cli i list --mine --limit 10
linear-cli i list --team "<team>" --group-by state
linear-cli i list --team "<team>" --since "-7d" --count-only
```

### Get

**Syntax**: `linear-cli issues get [OPTIONS] <ID>...`

```bash
linear-cli i get <prefix>-123                    # By identifier
linear-cli i get <prefix>-1 <prefix>-2 <prefix>-3          # Multiple issues
linear-cli i get <prefix>-123 --comments         # Include comments
linear-cli i get <prefix>-123 --history          # Include activity history
linear-cli i get <prefix>-123 --output json      # JSON output
```

### Update

**Syntax**: `linear-cli issues update [OPTIONS] <ID>`

ID is a **positional argument**. Use `-T` (capital T) for title, NOT `--title` on create.

| Flag | Short | Description |
|------|-------|-------------|
| `--title` | `-T` | New title (capital T!) |
| `--description` | `-d` | New description |
| `--priority` | `-p` | New priority |
| `--state` | `-s` | New state name |
| `--assignee` | `-a` | New assignee |
| `--labels` | `-l` | Labels to set (repeatable) |
| `--due` | | Due date (or `"none"` to clear) |
| `--estimate` | `-e` | Points (or `0` to clear) |
| `--project` | | Project name (or `"none"` to remove) |
| `--data` | | Raw JSON fields for anything not covered |

```bash
linear-cli i update <prefix>-123 -s "Done"
linear-cli i update <prefix>-123 -T "New Title" -p 1
linear-cli i update <prefix>-123 -a "me" --due "+3d"
linear-cli i update <prefix>-123 --project "My Project"

# When --state fails with Argument Validation Error, use state UUID:
linear-cli i update <prefix>-123 --data '{"stateId": "24d2846f-70b2-478f-bb03-a4026364f0ae"}'

# Move to a different team (no --team flag on update):
linear-cli i update IT-2 --data '{"teamId": "28e7bb33-754e-4638-9efb-a17a3f382d03"}'
```

### Quick Actions

```bash
linear-cli i start <prefix>-123    # Set "In Progress" + assign to me
linear-cli i stop <prefix>-123     # Return to backlog
linear-cli i close <prefix>-123    # Mark as Done
linear-cli i assign <prefix>-123 "me"
```

### Search

```bash
linear-cli search issues "auth bug"
linear-cli search projects "backend"
```

## Comments

```bash
# List comments on an issue
linear-cli comments list <prefix>-123

# Create comment — issue ID is positional, body is --body or -b
linear-cli comments create <prefix>-123 --body "Comment text"
linear-cli comments create <prefix>-123 --body "$(cat <<'EOF'
Multi-line comment with **markdown**.
EOF
)"

# Reply to a comment
linear-cli comments create <prefix>-123 --body "Reply" --parent-id COMMENT-ID
```

## Projects

```bash
# List / get
linear-cli projects list
linear-cli projects list --team "<team>"
linear-cli projects get PROJECT-ID

# Create — name is a POSITIONAL argument
linear-cli projects create "Project Name" --team "<team>"
linear-cli projects create "Project Name" --team "<team>" --description "Description"

# Update
linear-cli projects update PROJECT-ID --name "New Name"
linear-cli projects update PROJECT-ID --status "started"
```

## Cycles

```bash
linear-cli cycles list
linear-cli cycles list --team "<team>"
```

## Teams & Users

```bash
linear-cli teams list
linear-cli users list
linear-cli whoami                    # Current authenticated user
```

## Bulk Operations

```bash
# Update state of multiple issues
linear-cli bulk update-state -s "Done" <prefix>-213 <prefix>-214 <prefix>-215

# Assign multiple issues
linear-cli bulk assign --user "me" <prefix>-213 <prefix>-214

# Add label to multiple issues
linear-cli bulk label --add "infrastructure" <prefix>-213 <prefix>-214

# Unassign multiple issues
linear-cli bulk unassign <prefix>-213 <prefix>-214

# Dry-run to preview
linear-cli bulk update-state -s "Done" <prefix>-213 --dry-run
```

## Output & Filtering

```bash
# Output formats
--output table    # Default, human-readable
--output json     # Structured JSON
--output ndjson   # One JSON object per line

# Filtering (all commands)
--filter "state.name=In Progress"       # Exact match
--filter "priority!=4"                  # Not equal
--filter "title~=migration"            # Case-insensitive contains
--filter "state.name=Done" --filter "assignee.name~=ruslan"  # AND logic

# JSON field selection
--fields "identifier,title,state.name"

# Template formatting
--format '{{identifier}} {{title}}'

# Pagination
--limit 50 --all                       # Fetch all pages
```

## Attachments (GraphQL API)

For operations not covered by CLI subcommands:

```bash
# List attachments on an issue
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issue(id: \"ISSUE-ID\") { attachments { nodes { id title url } } } }"}'
```

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| `issues create --title "X"` | Title is **positional**: `issues create "X"` |
| `--status "Done"` | Flag is **`--state`** (or `-s`), not `--status` |
| `--team "<prefix>"` | Use full **team name**: `--team "<team>"` |
| `--team "<team>"` on `update` | No `--team` on update. Use `--data '{"teamId":"UUID"}'` |
| `--state "Done"` fails with validation error | Use `--data '{"stateId":"UUID"}'` with state UUID |
| `--label "nonexistent"` | Label must exist. Check with `linear-cli labels list` first |
| `issues show <prefix>-123` | Subcommand is **`get`**, not `show` |
| `--title "X"` on `update` | Use **`-T`** (capital T) or `--title` — works on update only, NOT create |

## Team Name → Key Mapping

| Team Name | Key | Team ID |
|-----------|-----|---------|
| <team> | <prefix> | `28e7bb33-754e-4638-9efb-a17a3f382d03` |
| IT | IT | `65d05685-3a1f-45b9-b1e2-74fbc550b9c3` |
| <team> | <prefix> | `2fc306b6-3ac4-4c1d-bd4e-c8e75bfd135c` |
| <team> | <prefix> | `f4e00be2-8aa0-4604-901a-84355715fba3` |
| Data | <prefix> | `672f3ecf-01fe-412e-84f6-ad9598645dfc` |
| <prefix> | <prefix> | `1108ae95-da16-4c3e-ae91-ca941b2c94de` |

## Workflow State IDs (<team> Team)

Use these UUIDs with `--data '{"stateId": "..."}'` when `--state "Name"` fails:

| State | Type | UUID |
|-------|------|------|
| Backlog | backlog | `bdee81cc-a03a-47d9-afec-3f4b69c3f7c3` |
| Todo | unstarted | `9d65c168-66c7-4c03-848e-3ad39d782947` |
| In Progress | started | `830d8517-edd6-46d1-99b7-31a2279ff52b` |
| In Review | started | `e03db58f-babf-4686-b747-e0e6d3694a62` |
| Done | completed | `24d2846f-70b2-478f-bb03-a4026364f0ae` |
| Canceled | canceled | `eb06b8ab-4f74-4f61-a59f-d77a920679da` |
| Duplicate | canceled | `764075d1-629e-4534-9154-385c3f488fda` |

## Tips

- Priority values: 0 (none), 1 (urgent), 2 (high), 3 (normal), 4 (low)
- Due date formats: `today`, `tomorrow`, `+3d`, `+1w`, `YYYY-MM-DD`, `"none"` to clear
- Use `--dry-run` on create/update to preview without making changes
- Use `--quiet` and `--id-only` for scripting
- Use `--no-pager` to prevent interactive pager in non-TTY contexts
