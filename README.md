# claude-skills

Personal Claude Code skill bundle. Install via marketplace:

```sh
claude /plugin marketplace add github:rkhozinov/claude-marketplace
claude /plugin install claude-skills
```

## Skills

| Skill | What |
|-------|------|
| `gh` | GitHub CLI reference + multi-account auth recipes |
| `grafana` | Grafana Cloud / IRM / OnCall API access |
| `slack-cli` | Slack via local Python CLI (`bin/slack`) |
| `linear-cli` | Linear operations through `linear-cli` |
| `issue` | Create Linear issues from natural language |
| `things3` | Things 3 (macOS) todo management |
| `archive-sessions` | Compress old Claude Code session transcripts |
| `claude-diff` | Open Zed / PyCharm visual diff for git changes |
| `skill-creator` | Author, evaluate, and benchmark skills |
| `awk-sed` | awk/sed one-liner reference for shell pipeline transforms |
| `matter-cli` | Matter reading-app CLI: reading list, highlights, tags, search |
| `brainstorming` | Explore intent and design before implementation |
| `systematic-debugging` | Evidence-first debugging: reproduce, isolate, root-cause |
| `test-driven-development` | Red-green-refactor loop for features and bugfixes |

## Attribution

`brainstorming`, `systematic-debugging`, and `test-driven-development` are vendored
from [obra/superpowers](https://github.com/obra/superpowers) (MIT, © Jesse Vincent),
lightly edited to drop cross-references to skills not bundled here. Full license text
in [`LICENSE-superpowers`](LICENSE-superpowers).
