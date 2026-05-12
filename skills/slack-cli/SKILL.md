---
name: slack-cli
description: Reference skill for Slack operations via a local Python CLI (`bin/slack`) that wraps the Slack Web API with a user OAuth token (xoxp). Replaces the Slack MCP plugin to avoid 3k+ tokens of tool schemas. Covers mentions, DMs, threads, send/reply, search, file download, and a raw API escape hatch. Use when the user wants to send/search/read Slack from the terminal or agent without loading the MCP plugin.
user_invocable: false
---

# Slack CLI Reference

Wraps the Slack Web API behind a single Python CLI: `~/.claude/skills/slack-cli/bin/slack`.

The CLI is a [PEP 723 inline-script](https://peps.python.org/pep-0723/) Python file run via `uv run --script` (shebang). First call installs `requests` to a uv-managed venv (~9ms thereafter).

Auth is a user OAuth token (xoxp) issued by the user's "Claude MCP" Slack app (App ID `<APP_ID>`, <org> workspace `<WORKSPACE_ID>`). Acts as the user — full search, DM access, posts as them.

## Token

Stored in macOS Keychain under service `slack-xoxp`. The CLI fetches at runtime; no shell handling needed. Override for one-off calls with `SLACK_XOXP=xoxp-… slack …`.

If the keychain entry is missing or stale, recreate it:

```bash
security add-generic-password -a "$USER" -s slack-xoxp -w 'xoxp-…' -U
```

## Granted user scopes

`search:read`, `channels:history`, `groups:history`, `im:history`, `mpim:history`, `chat:write`, `users:read`, `users:read.email`, `files:read`.

If a method returns `missing_scope`, add the scope at https://api.slack.com/apps/<APP_ID>/oauth and reinstall.

## Usage

```bash
slack whoami                                  # auth.test (sanity check)
slack mentions [-n 20]                        # @mentions of self, newest first
slack dms      [-n 15] [--group]              # latest msg per 1:1 DM (--group adds mpim)
slack thread   <channel-id> <thread-ts>       # full thread
slack reply    <channel-id> <thread-ts> <txt> # post reply in thread
slack send     <channel-id> <txt>             # post top-level message
slack search   '<query>' [-n 20]              # slack-search-bar syntax
slack file     <file-id> [-o <path>]          # download a file by id (default: ./<name>; -o - for stdout)
slack raw      <method> [k=v …] [--post]      # escape hatch: any Web API method
slack <cmd> --json                            # raw API JSON instead of formatted table
```

`<channel-id>` is the `C…`/`G…`/`D…` id (or `U…` for DMs — Slack accepts user IDs as channel for `chat.postMessage`). Use `slack raw conversations.list types=public_channel,private_channel limit=1000` to discover IDs by name.

`<thread-ts>` is the `epoch.microseconds` string from a permalink (`p1778164397756779` → `1778164397.756779`).

Output format:
- Default: numbered table — first column is `[N]`, last column is the permalink (mentions/search) or text (dms). Reference rows by index when iterating ("open thread #3").
- `--json`: raw Slack response, suitable for `| jq`.

## Common patterns

```bash
# triage mentions, then dive into one
slack mentions -n 20
slack thread C0AQ7M5R36W 1778164397.756779

# search a channel
slack search 'in:#engineering deploy after:2026-04-01' -n 20

# discover file IDs in a thread, then download
slack thread C0… 1778… --json | jq -r '.messages[].files[]? | .id + "\t" + .name'
slack file F0B3R03TR4G                        # writes ./id_argus_a6000.pub
slack file F0B2UKBUC86 -o ~/.ssh/             # writes ~/.ssh/id_argus_a6000
slack file F0… -o -                           # stream to stdout for piping

# DM a user by email
UID=$(slack raw users.lookupByEmail email=alice@example.com | jq -r '.user.id')
slack send "$UID" "ping — got a sec?"

# react to a message
slack raw reactions.add channel=C… timestamp=1714… name=thumbsup --post
```

Slack search syntax mirrors the search bar: `from:@user`, `in:#channel`, `before:`, `after:`, `has:link`, etc. `is:mention` is **not** a self-mention filter — it matches the literal word "mention". Use `<@USER_ID>` (or just `slack mentions`) instead.

## Pitfalls

- **`UID` is readonly in bash.** If you ever drop back to a `while read -r CHAN UID` loop, rename to `PEER_ID` — bash refuses the assignment with `failed to change user ID: operation not permitted`.
- **rtk hook wraps `curl`** in Claude Code sessions and appends `[Tee log: …]` to stdout, breaking `jq`. The Python CLI doesn't shell out to curl, so it's immune. If you do call curl directly, use `rtk proxy curl …`.
- **`search.messages` is rate-limited tier 2** (~20/min). `users.info` is tier 3 (~50/min). The CLI memoizes user lookups per-invocation, but a `dms -n 100` cold run can still hit the cap — re-run after a minute.
- **`as_user` is deprecated**; xoxp posts as the token owner automatically.
- **DMs**: post to user ID directly (`slack send U… …`); no need to open IM first.
- **File URLs need bearer auth, not cookies.** `https://files.slack.com/files-pri/…` returns HTTP 200 with a Slack login *page* (HTML) if you fetch it without `Authorization: Bearer $xoxp`. The CLI handles this — bare `curl` does not. Easy to mistake for a successful download.
- **Sensitive content in Slack is already exposed.** SSH private keys, API tokens, .env files, credentials posted as Slack attachments live in channel history, search index, mobile caches, and any workspace export. Downloading them later doesn't undo that — treat as compromised and rotate.

## Escape hatch

For Web API methods the CLI doesn't wrap natively (canvases, admin scopes, file uploads, etc.), use:

```bash
slack raw <method> key=val key=val            # GET-style query params
slack raw <method> key=val --post             # POST as JSON body
```

This is a thin shim over `requests.get/post` — same auth, same `.ok` enforcement, just no formatting. Pipe through `jq`.

## Re-enabling the MCP plugin

If a workflow needs admin-only Slack tools that this CLI doesn't cover, temporarily flip the plugin back on:

```bash
# enable
jq '.enabledPlugins."slack@claude-plugins-official" = true' ~/.claude/settings.json | sponge ~/.claude/settings.json
# or use /plugin
```

## Source

- CLI: `~/.claude/skills/slack-cli/bin/slack` — single Python file, ~250 lines, argparse subcommands.
- Token retrieval: `security find-generic-password -a "$USER" -s slack-xoxp -w` (or `SLACK_XOXP` env override).
- Adding a subcommand: edit the script, add an `argparse` subparser + `cmd_*` function. No packaging, no install step.
