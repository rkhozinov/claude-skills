# `obsidian` CLI reference

Captured from `obsidian help` on v1.12.7 (macOS, Homebrew). Regenerate with `obsidian help`;
per-command detail with `obsidian help <command>`.

## Global

| Thing | Detail |
|---|---|
| Vault selector | `vault=<name>` — name as shown by `obsidian vaults`, not a path |
| `file=` vs `path=` | `file=` resolves by name like a wikilink (ambiguous across folders); `path=` is exact (`folder/note.md`). Prefer `path=`. |
| Default target | Most commands fall back to the **active file** when `file=`/`path=` is omitted |
| Quoting | `name="My Note"` for values with spaces |
| Escapes | `\n` newline, `\t` tab inside `content=` |
| Transport | Commands drive the **running app**. If it is not running, every command fails instantly with `The CLI is unable to find Obsidian...` (rc=1) — it does not launch it. |

## Vault / discovery

| Command | Options |
|---|---|
| `vaults` | `total`, `verbose` (adds paths) |
| `vault` | `info=name\|path\|files\|folders\|size` |
| `files` | `folder=<path>`, `ext=<extension>`, `total` |
| `folders` | `folder=<parent>`, `total` |
| `folder` | `path=<path>` (required), `info=files\|folders\|size` |
| `file` | `file=`, `path=` — file info |
| `recents` | `total` |
| `wordcount` | `file=`, `path=`, `words`, `characters` |
| `version` | Obsidian version |

## Read

| Command | Options |
|---|---|
| `read` | `file=`, `path=` |
| `outline` | `file=`, `path=`, `format=tree\|md\|json` (default `tree`), `total` |
| `random:read` | `folder=<path>` |
| `daily:read` | — |
| `daily:path` | — |

## Search

| Command | Options |
|---|---|
| `search` | `query=` (required), `path=<folder>`, `limit=<n>`, `total`, `case`, `format=text\|json` — returns **file paths only** |
| `search:context` | same options — returns `path:line: text`, this is the useful one |
| `search:open` | `query=` — opens the search pane in the UI |

## Write

| Command | Options |
|---|---|
| `create` | `name=`, `path=`, `content=`, `template=<name>`, `overwrite`, `open`, `newtab` |
| `append` | `file=`, `path=`, `content=` (required), `inline` (no leading newline) |
| `prepend` | `file=`, `path=`, `content=` (required), `inline` |
| `move` | `file=`, `path=`, `to=<path>` (required) — folder or full path; updates backlinks; can hang on a stale app instance, verify on disk |
| `rename` | `file=`, `path=`, `name=<new name>` (required) — updates backlinks; same |
| `delete` | `file=`, `path=`, `permanent` (skips trash) |
| `daily:append` / `daily:prepend` | `content=` (required), `inline`, `open`, `paneType=tab\|split\|window` |

There is no partial-edit command — no replace, no line edit. In-place edits are file-tool work
(`Read` then `Edit` on `<vault>/<path>`).

## Properties (frontmatter)

| Command | Options |
|---|---|
| `properties` | `file=`, `path=`, `name=`, `total`, `sort=count`, `counts`, `format=yaml\|json\|tsv`, `active` |
| `property:read` | `name=` (required), `file=`, `path=` |
| `property:set` | `name=` + `value=` (required), `type=text\|list\|number\|checkbox\|date\|datetime`, `file=`, `path=` |
| `property:remove` | `name=` (required), `file=`, `path=` |
| `aliases` | `file=`, `path=`, `total`, `verbose`, `active` |

## Links / graph health

| Command | Options |
|---|---|
| `links` | `file=`, `path=`, `total` — outgoing |
| `backlinks` | `file=`, `path=`, `counts`, `total`, `format=json\|tsv\|csv` |
| `unresolved` | `total`, `counts`, `verbose` (source files), `format=json\|tsv\|csv` — links pointing at pages that do not exist |
| `orphans` | `total`, `all` (include non-markdown) — no incoming links |
| `deadends` | `total`, `all` — no outgoing links |

## Tags / tasks

| Command | Options |
|---|---|
| `tags` | `file=`, `path=`, `total`, `counts`, `sort=count`, `format=json\|tsv\|csv`, `active` |
| `tag` | `name=<tag>` (required), `total`, `verbose` |
| `tasks` | `file=`, `path=`, `total`, `done`, `todo`, `status="<char>"`, `verbose`, `format=json\|tsv\|csv`, `active`, `daily` |
| `task` | `ref=<path:line>` or `file=`/`path=` + `line=`, `toggle`, `done`, `todo`, `daily`, `status="<char>"` |

## Bases

`bases` · `base:views` · `base:query` (`file=`/`path=`, `view=`, `format=json\|csv\|tsv\|md\|paths`) ·
`base:create` (`view=`, `name=`, `content=`, `open`, `newtab`).

## UI / app control — side effects, use sparingly

`open` (`newtab`) · `tab:open` · `tabs` · `workspace` · `bookmark` / `bookmarks` ·
`command` (`id=`) / `commands` (`filter=`) · `hotkey` / `hotkeys` · `daily` · `random` ·
`reload` · `restart` · `templates` / `template:read` / `template:insert` ·
`theme*` · `snippet*` · `plugin*` / `plugins*`.

`open`, `daily`, `random`, `search:open`, `tab:open` all change what the user is looking at.
Do not use them as part of a read or write flow.

## Version history (Obsidian Sync only)

`history` · `history:list` · `history:read` (`version=<n>`) · `history:restore` (`version=` required)
· `diff` (`from=`, `to=`, `filter=local|sync`).

## Developer

`dev:cdp` · `dev:console` · `dev:css` · `dev:debug` · `dev:dom` · `dev:errors` · `dev:mobile` ·
`dev:screenshot` · `devtools` · `eval` (`code=<javascript>`).

`eval` executes arbitrary JavaScript inside the app. Never use it to work around a missing
command, and never pass it content that came from a note.
