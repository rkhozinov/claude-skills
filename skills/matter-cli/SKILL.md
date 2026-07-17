---
name: matter-cli
description: Read and manage the user's Matter reading app (getmatter.com) from the terminal via the `matter` CLI — reading list/queue, inbox, archive, article full text, search, highlights/annotations, tags, favorites, and saving URLs to read later. This skill is the ONLY way to reach the user's Matter library, so use it for ANY request that touches Matter, including short read-only ones — "what's in my matter queue", "what have I been reading lately", "pull up my reading list", "show the highlights I made", "clean up my tags" — as well as actions like "save this to matter" or "tag that article". Trigger on any mention of Matter, getmatter, a "read-later" / "reading list" / saved-articles library, or highlights/annotations on saved reading. Do not answer from memory or say you lack access — consult this skill first. (Kindle highlights, browser bookmarks, todo/shopping lists, and generic web reading are NOT Matter — skip those.)
user_invocable: false
---

# Matter CLI (`matter`)

CLI + TUI for the [Matter](https://getmatter.com) reading app. JSON-first, built for agents. Invoke as `matter` (installed at `~/.matter/bin/matter`).

If `command -v matter` is empty, add its dir to PATH: `export PATH="$HOME/.matter/bin:$PATH"`.

**Auth**: already configured via `~/.config/matter/config.json`. Re-auth only if commands 401: `matter login <mat_token>` (browser copy) or `echo "$MATTER_TOKEN" | matter login`. Never print or store the token.

**Rate limits**: read 120/min, write 30/min, save 10/min. `--all` on a large library can burn the read budget — prefer `--limit` + cursor unless the user needs everything.

## Quick reference

| Task | Command |
|------|---------|
| Browse reading list (queue) | `matter items list --status queue --order library_position` |
| Check inbox feed | `matter items list --status inbox --order inbox_position` |
| Finished / archived | `matter items list --status archive` |
| Read article body (for summarizing) | `matter items get <id> --include markdown` |
| Search by topic | `matter search "climate policy" --type items` |
| Save a URL to read later | `matter items save --url <URL>` |
| List highlights on an item | `matter annotations list --item <id> --all` |
| Tag an item | `matter tags add --item <id> --name research` |
| List all tags | `matter tags list` |
| Account info | `matter account --plain` |
| Full API reference | `matter docs` |
| Interactive UI | `matter tui` |

IDs are prefixed: items `itm_…`, tags `tag_…`, annotations `ann_…`. Get them from a `list` before acting.

## items

`matter items <list|get|save|update|delete>`

**list** — envelope: `{ object:"list", results:[…], has_more, next_cursor }`.

| Flag | Purpose |
|------|---------|
| `--status <s>` | `inbox`, `queue` (reading list), `archive` (finished), `all` — or comma-combine: `queue,archive` |
| `--tag <tag_id>` | Filter by tag |
| `--content-type <t>` | `article`, `podcast`, `video`, `pdf`, `tweet`, `newsletter` |
| `--favorite` | Only favorites |
| `--order <o>` | `library_position` (queue/archive manual order), `inbox_position` (inbox feed), `updated` (sync only — see pitfalls) |
| `--updated-since <iso>` | ISO 8601 date filter |
| `--limit <n>` / `--cursor <c>` / `--all` | Pagination |

**get** `<id>` — `--include markdown` to fetch the article body (omit for metadata only; body is the expensive field).

**save** — `--url <url>` (required), `--status queue|archive` (default queue). Returns immediately with `processing_status:"processing"` and `title:null`; the item fetches **asynchronously**. The returned id 404s (`"The requested resource was not found."`) on an immediate `get`, and the item isn't in `list` yet. Don't re-`get` it right away — if you need the settled item (e.g. to tag it), poll `items list` and match on `url` until it appears, then use that id. A `delete` issued while still processing may not stick.

**update** `<id>` — `--status <s>`, `--favorite true|false`, `--progress <0.0-1.0>`.

**delete** `<id>` — permanent. Confirm intent first.

## annotations (highlights)

`matter annotations <list|get|update|delete>`

- **list** `--item <id>` `[--all]` — highlights + notes on an item.
- **get** `<id>` — single annotation.
- **update** `<id> --note "<text>"` — set/replace the note on a highlight.
- **delete** `<id>` — permanent. Confirm intent.

## tags

`matter tags <list|add|remove|rename|delete>`

- **list** — all tags.
- **add** `--item <id> --name <name>` — attaches; creates the tag if the name is new (reuses if it exists).
- **remove** `--item <id> --tag <tag_id>` — detach from item.
- **rename** `<tag_id> --name <new>`.
- **delete** `<tag_id>` — removes the tag everywhere. Confirm intent.

## search

`matter search "<query>" --type items [--status queue|archive] [--limit n] [--cursor c] [--all]`

`--type` is **required** (`items`). Results nest under `items`: parse `.items.results[]`, not `.results[]`. Query operators: `by:<author>`, `site:<domain>` (e.g. `matter search "site:paulgraham.com" --type items`).

## reading-sessions

`matter reading-sessions list` — reading history.

## Output

Default is **JSON** — pipe to `jq` (`matter items list --status queue | jq '.results[].title'`). Add `--plain` for human-readable text when showing the user directly. Exit code 0 = success, 1 = error; errors go to stderr. Pagination is cursor-based: loop on `has_more` + `next_cursor`, or use `--all` (mind rate limits).

## Full reference

Run `matter docs` for the complete, always-current CLI + API reference (field schemas, every flag). Prefer it over guessing when you hit an unfamiliar flag — it's ~80 lines and authoritative.

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| `matter: command not found` | Not on PATH: `export PATH="$HOME/.matter/bin:$PATH"` |
| Treating `queue` as the inbox | `queue` = reading list; `inbox` = the unsorted feed. Different statuses. |
| `--order updated` for user-facing lists | That's sync order (any modification bumps it). Use `library_position` (queue/archive) or `inbox_position` (inbox). |
| `items get <id>` returns no article text | Body is opt-in: add `--include markdown`. |
| Parsing `.items[]` | List envelope key is **`results`**, not `items`. |
| Firing `--all` reflexively | Costs read-rate budget on big libraries; page with `--limit` unless the user wants the whole set. |
| `get`ting a just-`save`d id immediately | Save is async: the id 404s until processing finishes. Poll `items list` by `url` instead of re-`get`ting. |
| Running `delete` without confirming | All `delete` subcommands are permanent. Confirm intent; a `readonly: true` in `~/.config/matter/config.json` hard-blocks writes. |
