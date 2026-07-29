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
| `linear` | Linear operations through `linear-cli` |
| `issue` | Create Linear issues from natural language |
| `skill-creator` | Author, evaluate, and benchmark skills |
| `matter-cli` | Matter reading-app CLI: reading list, highlights, tags, search |
| `brainstorming` | Explore intent and design before implementation |
| `systematic-debugging` | Evidence-first debugging: reproduce, isolate, root-cause |
| `test-driven-development` | Red-green-refactor loop for features and bugfixes |
| `ponytail` | Lazy-senior-dev mode: YAGNI, stdlib first, shortest working diff |
| `atdd` | Four-layer acceptance testing: spec / DSL / protocol driver / SUT |

## Attribution

Some skills here are vendored from upstream projects:

| Skills | Upstream | License |
|---|---|---|
| `brainstorming`, `systematic-debugging`, `test-driven-development` | [obra/superpowers](https://github.com/obra/superpowers) | MIT, © Jesse Vincent — [`LICENSE-superpowers`](LICENSE-superpowers) |
| `ponytail` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | MIT, © DietrichGebert — [`LICENSE-ponytail`](LICENSE-ponytail) |

Exact upstream refs and commit SHAs are pinned in [`vendor.json`](vendor.json).

`atdd` is not vendored — it is written here, synthesizing Dave Farley's four-layer
acceptance testing model with the isolation, naming, and phase-gate rules from
[AAID](https://github.com/dawid-dahl-umain/augmented-ai-development) (MIT, © Dawid Dahl).
AAID's own `aaid-bdd` plugin is the fuller, longer treatment if you want it upstream.

Local edits on top of upstream: cross-references to skills not bundled here are
rewritten, upstream eval fixtures are pruned, and keyword-stuffed descriptions are
shortened (they cost context in every session, and these skills are invoked
deliberately rather than auto-triggered).

To pull newer upstream versions, bump `ref` in `vendor.json` and run:

```sh
scripts/vendor-refresh.sh            # all sources
scripts/vendor-refresh.sh ponytail   # just one
```

The script re-clones, re-applies every local edit, rewrites the pinned SHA to what it
actually fetched, and leaves the result in the worktree for `git diff` review. It never
commits.
