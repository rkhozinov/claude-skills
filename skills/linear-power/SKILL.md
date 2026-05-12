---
name: linear-power
description: Advanced Linear ops — projects, cycles, bulk updates (multiple issues at once), team transfers, advanced filters with --filter/--fields/--format templates, attachments, and raw GraphQL fallback via --data. Use this when the basic `linear` skill isn't enough — e.g. closing 10 issues at once, moving issues between teams, filtering by complex conditions, or working with projects/cycles. For everyday single-issue create/comment/update, use the `linear` skill.
user_invocable: false
---

# Linear CLI — Power User

Same binary as the `linear` skill: `${CLAUDE_PLUGIN_ROOT}/skills/linear/bin/linear-cli` (one copy lives in `skills/linear/bin/`, both skills reference it). All everyday operations from `linear` also work here — this doc covers the advanced surface.

## Env defaults (reminder)

`LINEAR_DEFAULT_TEAM`, `LINEAR_DEFAULT_PROJECT` — apply to commands that take `--team` / `--project`. Override per-invocation with the flag.

## Projects

```bash
linear-cli projects list
linear-cli projects list --team "<team>"
linear-cli projects get <PROJECT-ID-OR-NAME>

linear-cli projects create "Project Name" --team "<team>" --description "Why"
linear-cli projects update <PROJECT-ID> --name "Renamed"
linear-cli projects update <PROJECT-ID> --status started   # planned|started|paused|completed|canceled
```

## Cycles

```bash
linear-cli cycles list
linear-cli cycles list --team "<team>"
```

## Bulk operations

Operate on multiple issues in one command. Each issue is resolved independently; failures don't abort the batch. `--dry-run` previews without mutating.

```bash
# Set state on many
linear-cli bulk update-state -s "Done" <prefix>-213 <prefix>-214 <prefix>-215

# Assign many
linear-cli bulk assign --user me <prefix>-213 <prefix>-214

# Unassign
linear-cli bulk unassign <prefix>-213 <prefix>-214

# Labels (per-issue, label must exist in that team)
linear-cli bulk label --add "infra" <prefix>-213 <prefix>-214
linear-cli bulk label --remove "stale" <prefix>-213

# Dry-run any of the above
linear-cli bulk update-state -s "Done" <prefix>-213 --dry-run
```

## Transfer / move

```bash
linear-cli issues transfer <prefix>-123 "IT"          # move to a different team
linear-cli issues move <prefix>-123 "Project Name"    # move to a different project
```

No `--team` flag on `issues update` — to change team programmatically use `--data '{"teamId":"UUID"}'`. Use `teams list` to look up team UUIDs.

## Search

```bash
linear-cli search issues "auth bug"            # full-text issue search
linear-cli search projects "platform"          # project search
```

## Advanced filtering on `issues list` / `get`

`--filter` accepts repeated key=value/!=/~= expressions (AND between flags), with nested key paths:

```bash
# Exact match
linear-cli i list --team "<team>" --filter "state.name=In Progress"

# Not equal
linear-cli i list --team "<team>" --filter "priority!=4"

# Case-insensitive contains
linear-cli i list --team "<team>" --filter "title~=migration"

# AND across flags
linear-cli i list --team "<team>" \
  --filter "state.name=Done" \
  --filter "assignee.name~=ruslan"
```

`--fields` extracts a column subset for JSON / table output; `--format` does jinja-lite `{{key.subkey}}` interpolation per row.

```bash
linear-cli i list --team "<team>" --fields "identifier,title,state.name"
linear-cli i list --mine --format '{{identifier}}  {{title}}'
linear-cli i list --team "<team>" --output ndjson > issues.jsonl
```

## Pagination

```bash
linear-cli i list --team "<team>" --limit 200          # cap at 200
linear-cli i list --team "<team>" --all                # fetch every page
```

## Raw `--data` escape hatch

When a CLI flag can't express what you need (rare state name collisions, fields not surfaced as flags), pass any `IssueUpdateInput` / `IssueCreateInput` field as JSON. It is shallow-merged into the input.

```bash
# State name "Done" exists in multiple teams; force the exact UUID:
linear-cli i update <prefix>-123 --data '{"stateId":"24d2846f-70b2-478f-bb03-a4026364f0ae"}'

# Cross-team transfer via update (alternative to `issues transfer`):
linear-cli i update IT-2 --data '{"teamId":"28e7bb33-754e-4638-9efb-a17a3f382d03"}'

# Attach external link metadata at creation time:
linear-cli i create "Bug" --team "<team>" --data '{"sortOrder": 1000.5}'
```

## Attachments

```bash
linear-cli attachments list <prefix>-123
```

For creation/deletion of attachments, fall back to direct GraphQL — see the next section.

## Direct GraphQL fallback

For features not covered above (custom views, integrations, webhooks, organization-level operations):

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issue(id: \"<prefix>-123\") { attachments { nodes { id title url } } } }"}'
```

The CLI's GraphQL client (`gql` function in the binary) reads the same `$LINEAR_API_KEY` and may be easier to call from a Python REPL than `curl`.

## Cache

Team / user / project / label metadata is cached at `~/.cache/linear-cli/cache.json` for 24h. Stale lookups (new team, renamed label) — delete the file to force refetch:

```bash
rm -f ~/.cache/linear-cli/cache.json
```

## Workflow state UUIDs (<team>)

Use these with `--data '{"stateId": "..."}'` when `--state "Name"` is ambiguous or fails validation:

| State | Type | UUID |
|-------|------|------|
| Backlog | backlog | `bdee81cc-a03a-47d9-afec-3f4b69c3f7c3` |
| Todo | unstarted | `9d65c168-66c7-4c03-848e-3ad39d782947` |
| In Progress | started | `830d8517-edd6-46d1-99b7-31a2279ff52b` |
| In Review | started | `e03db58f-babf-4686-b747-e0e6d3694a62` |
| Done | completed | `24d2846f-70b2-478f-bb03-a4026364f0ae` |
| Canceled | canceled | `eb06b8ab-4f74-4f61-a59f-d77a920679da` |
| Duplicate | canceled | `764075d1-629e-4534-9154-385c3f488fda` |

## Team UUIDs (selected)

| Team | Key | UUID |
|------|-----|------|
| <team> | <prefix> | `28e7bb33-754e-4638-9efb-a17a3f382d03` |
| IT | IT | `65d05685-3a1f-45b9-b1e2-74fbc550b9c3` |
| <team> | <prefix> | `2fc306b6-3ac4-4c1d-bd4e-c8e75bfd135c` |
| <team> | <prefix> | `f4e00be2-8aa0-4604-901a-84355715fba3` |
| Data | <prefix> | `672f3ecf-01fe-412e-84f6-ad9598645dfc` |
| <prefix> | <prefix> | `1108ae95-da16-4c3e-ae91-ca941b2c94de` |

Full list via `linear-cli teams list`.

## Tips

- Use `--dry-run` on create/update/bulk to preview the payload before committing.
- `--quiet` suppresses output, `--id-only` prints only the identifier (<prefix>-123) per row — both useful in scripts.
- `--no-pager` keeps stdout flowing in non-TTY contexts.
