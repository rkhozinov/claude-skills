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

`search:read`, `channels:history`, `groups:history`, `im:history`, `mpim:history`, `channels:read`, `groups:read`, `chat:write`, `users:read`, `users:read.email`, `files:read`.

If a method returns `missing_scope`, add the scope at https://api.slack.com/apps/<APP_ID>/oauth and reinstall. Notably `react` needs `reactions:write` (not granted by default), and `channels` needs `channels:read`/`groups:read`.

## Usage

```bash
slack whoami                                  # auth.test (sanity check)
slack mentions [-n 20]                        # @mentions of self, newest first
slack dms      [-n 15] [--group] [--no-resolve]            # latest msg per 1:1 DM (--group adds mpim)
slack history  <channel> [-n 30] [--since 2d] [--cursor X] [--links] [--activity] [--no-resolve] [--warm]  # channel timeline, newest first
slack thread   <channel> <thread-ts> [-n 50] [--since 2d] [--cursor X] [--links] [--activity] [--no-resolve] [--warm]  # thread, oldest first
slack reply    <channel> <thread-ts> [txt] [--raw]   # post reply in thread
slack send     <channel> [txt] [--raw]               # post top-level message
#   send/reply take Markdown (auto-converted to Slack mrkdwn; --raw to skip) and
#   --text-file <path|->  (body from file or stdin; preferred — see below)
slack search   '<query>' [-n 20]              # slack-search-bar syntax
slack channels [--types …] [--sort name|popularity] [-n 100]   # list channels; warms the #name→id cache
slack users    '<query>' [-n 20]              # find users by name/handle/email (over the cache)
slack react    <channel> <ts> <emoji> [--remove]   # add/remove a reaction (needs reactions:write)
slack file     <file-id> [-o <path>]          # download a file by id (default: ./<name>; -o - for stdout)
slack raw      <method> [k=v …] [--post]      # escape hatch: any Web API method
slack <cmd> --json                            # raw API JSON instead of formatted output
```

`<channel>` accepts a `C…`/`G…`/`D…` id, `U…` (for DMs), **or a `#name` / `@user`** — names resolve to IDs through a persistent cache (see below). `<thread-ts>` is the `epoch.microseconds` string from a permalink (`p1778164397756779` → `1778164397.756779`).

### Name resolution & persistent cache

`history`/`thread`/`send`/`reply`/`react` accept `#channel-name` and `@user-name` as the channel arg; `users` and the output labeling resolve IDs back to names. Resolution is backed by an on-disk cache at `~/.cache/slack-cli/{users,channels}.json` (override base via `$XDG_CACHE_HOME`), so it is near-free after the first populate and survives the per-run rate cap. Warm it once:

```bash
slack channels              # bulk-loads every channel name→id (and caches it)
slack history "#engineering" -n 20     # now resolvable by name, no extra calls
```

`--no-resolve` ignores the cache for *output* (raw `U…`/`#C…`); name→id *input* still resolves (you can't call the API with a `#name`). `--warm` does one `users.list` walk up front for very busy channels. `--since 2d` (`30m`/`12h`/`2d`/`1w`) bounds reads to a recent window. `--links` appends a `↗ permalink` per message (built locally, zero API). `--activity` includes join/leave/topic system messages, which are **hidden by default**.

Output format:
- **`mentions` / `dms` / `search`** — numbered table; first column `[N]`, last column the permalink (mentions/search) or text (dms). Reference rows by index when iterating ("open thread #3"). `<@U…>`/`<#C…>` inside snippets are resolved to `@Name`/`#channel`.
- **`history` / `thread`** — clean per-message block (MCP-parity, ~8× smaller than raw JSON):
  ```
  [1781030359.145779] <person> (@<handle>) · Jun 10 19:17 (16h)
  done @Ruslan the reviews are in, thanks!
  :+1: 2  📎 1 file(s): error.log  ↳ Thread: 4 replies, 2 people, latest 15h ago
  ```
  Head line carries the raw `[ts]` — copy it straight into `slack thread`/`slack reply`. Names, `@`-mentions, `#`-channels resolved; timestamps in your Slack-profile TZ; reactions `:name: N`; files by name (not block trees); thread parents summarized. `history` is newest-first, `thread` oldest-first. When more remains, a final `next: --cursor <X>` line is printed — pass it back via `--cursor` to page.
  - `--no-resolve` skips all name lookups (raw `U…`/`#C…`, no `users.info`/`conversations.info` calls) — use for big/fast pulls or after hitting a rate cap.
  - `--warm` bulk-prefetches `users.list` once before resolving — cheaper than N per-user lookups on a busy channel.
- **`--json`** (every command) — raw Slack response, unchanged, suitable for `| jq`. `dms --json` rows carry `channel_id` (`D…`) + `user_id` (peer's `U…`, null for group) — so you can reply to a DM straight from the listing without a second lookup.

### Markdown is auto-converted to Slack mrkdwn

`send`/`reply` take **Markdown** and convert it to Slack's mrkdwn before posting, because Slack does **not** use CommonMark — bold is one `*star*` (not `**`), italic is `_underscore_`, links are `<url|label>`, and there are no headings. Without conversion, `**bold**` renders with literal asterisks (the classic bug). Conversions:

| You write (Markdown) | Sent to Slack |
|---|---|
| `**bold**`, `__bold__` | `*bold*` |
| `*italic*` | `_italic_` |
| `[label](url)` | `<url\|label>` |
| `# Heading` | `*Heading*` (bold line) |
| `~~strike~~` | `~strike~` |
| `` `code` ``, ```` ```fenced``` ```` | preserved as-is (not touched) |

Code spans/fences are protected, so `**` inside them survives. Pass **`--raw`** to skip conversion and send verbatim Slack mrkdwn (use it when you're hand-writing `*slack bold*` / `<url|label>` yourself).

### Sending text: prefer `--text-file`

For anything beyond a trivial one-liner, pass the body via `--text-file <path>` (or `--text-file -` for stdin) instead of the inline positional. Inline text goes through the shell, so backticks, `$(...)`, quotes, and newlines get mangled or trigger command substitution — the same class of failure that mandates `gh ... --body-file` over `--body`. The file path is read verbatim, no shell interpretation. Write the body with a Write tool to a tmpfile, then point `--text-file` at it.

```bash
# robust: multi-line / backticks / quotes survive intact
slack send D0AGABWHTSA --text-file /tmp/msg.md
slack reply C0… 1778164397.756779 --text-file -   <<'EOF'
done — see `Program.cs:477`. shipped in #709.
EOF
```

## Common patterns

```bash
# triage mentions, then dive into one
slack mentions -n 20
slack thread C0AQ7M5R36W 1778164397.756779

# read a channel by name, then page older (copy the printed next: --cursor)
slack channels                                # one-time: warm the #name→id cache
slack history "#engineering" -n 30
slack history "#engineering" -n 30 --cursor bmV4dF90czoxNzcy…

# what happened in the last day, with citeable links, skip the join noise
slack history "#engineering" --since 1d --links

# search a channel
slack search 'in:#engineering deploy after:2026-04-01' -n 20

# find a user's id by name, then DM them
slack users alice                             # → row with U… id
slack send "@Alice King" "ping — got a sec?"  # @name resolves via cache

# discover file IDs in a thread, then download
slack thread C0… 1778… --json | jq -r '.messages[].files[]? | .id + "\t" + .name'
slack file F0B3R03TR4G                        # writes ./id_argus_a6000.pub
slack file F0B2UKBUC86 -o ~/.ssh/             # writes ~/.ssh/id_argus_a6000
slack file F0… -o -                           # stream to stdout for piping

# DM a user by email (UID is readonly in bash — use PEER_ID)
PEER_ID=$(slack raw users.lookupByEmail email=alice@example.com | jq -r '.user.id')
slack send "$PEER_ID" "ping — got a sec?"

# reply to a DM straight from the listing (channel_id is in the json)
CH=$(slack dms --json | jq -r '.[] | select(.peer=="<person>") | .channel_id')
TS=$(slack dms --json | jq -r '.[] | select(.peer=="<person>") | .ts')
slack reply "$CH" "$TS" --text-file /tmp/reply.md

# react to a message (needs reactions:write scope)
slack react "#engineering" 1714… thumbsup
slack react "#engineering" 1714… thumbsup --remove
```

Slack search syntax mirrors the search bar: `from:@user`, `in:#channel`, `before:`, `after:`, `has:link`, etc. `is:mention` is **not** a self-mention filter — it matches the literal word "mention". Use `<@USER_ID>` (or just `slack mentions`) instead.

## Pitfalls

- **`UID` is readonly in bash.** If you ever drop back to a `while read -r CHAN UID` loop, rename to `PEER_ID` — bash refuses the assignment with `failed to change user ID: operation not permitted`.
- **rtk hook wraps `curl`** in Claude Code sessions and appends `[Tee log: …]` to stdout, breaking `jq`. The Python CLI doesn't shell out to curl, so it's immune. If you do call curl directly, use `rtk proxy curl …`.
- **`search.messages` is rate-limited tier 2** (~20/min). `users.info`/`conversations.info` are tier 3 (~50/min). Name resolution writes through to the persistent `~/.cache/slack-cli/` cache, so after a `slack channels` + a first warm pass it's near-zero lookups thereafter. Within a single run an in-memory cache also dedups every id. If you do hit the cap on a cold/busy channel: `--no-resolve` (raw ids, zero lookups), `--warm` (one `users.list` walk instead of N per-user calls), or re-run after a minute. The cache never expires automatically — re-run `slack channels` if a freshly-renamed channel won't resolve.
- **Timestamps render in the token owner's Slack-profile timezone** (`users.info` `tz`, fetched once per run and cached; local TZ fallback). Format is `Jun 11 14:32 (2h)` — absolute local time plus relative age.
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

- CLI: `~/.claude/skills/slack-cli/bin/slack` — single Python file, ~880 lines, argparse subcommands. Reads share one `format_message` formatter; name resolution is backed by in-memory + on-disk (`~/.cache/slack-cli/`) user/channel caches with `#name`/`@user` → id lookup.
- Token retrieval: `security find-generic-password -a "$USER" -s slack-xoxp -w` (or `SLACK_XOXP` env override).
- Adding a subcommand: edit the script, add an `argparse` subparser + `cmd_*` function. No packaging, no install step.
