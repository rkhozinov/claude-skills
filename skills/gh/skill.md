---
name: gh
description: GitHub CLI (gh) full reference. Covers multi-account setup, auth switching, issues, PRs, reviews, inline comments via API, code search, merge queues, and common pitfalls.
user_invocable: false
---

# GitHub CLI (`gh`) Reference

Use `gh` for all GitHub operations. Do NOT use the GitHub MCP plugin tools.

## Multi-Account Setup

### Accounts

| Account | Use | SSH Key |
|---------|-----|---------|
| `<work-account>` | Work (default) | `~/.ssh/id_rsa_work` → `github.com-work` |
| `rkhozinov` | Personal | `~/.ssh/id_rsa` → `github.com` |

The shell auto-switches to `<work-account>` on every `cd` and on shell startup via `ghswitch` in `~/.zshrc`.

### Auth Switching

```bash
# Manual switch (rarely needed — ghswitch handles it)
gh auth switch --user <work-account>
gh auth switch --user rkhozinov

# Check active account
gh auth status --active
```

### SSH Config

The `~/.ssh/config` maps hosts to keys:

- `github.com` → personal key (`id_rsa`)
- `github.com-work` → work key (`id_rsa_work`)

<org> repo remotes use `git@github.com-work:<org>/repo.git`.

## Issues

```bash
# List issues
gh issue list
gh issue list --state closed --limit 20
gh issue list --label "bug" --assignee "@me"

# View issue details
gh issue view 123
gh issue view 123 --json title,body,comments

# Create issue
gh issue create --title "Title" --body "Description"
gh issue create --title "Title" --body "Description" --label "bug" --assignee "user"

# Comment / close / reopen
gh issue comment 123 --body "Comment text"
gh issue close 123 --reason "completed"
gh issue reopen 123

# Search issues (cross-repo)
gh search issues "query" --repo owner/repo
gh search issues "query" --owner <org> --state open
```

## Pull Requests

```bash
# List PRs
gh pr list
gh pr list --state merged --limit 10
gh pr list --author "@me"

# View PR details
gh pr view 123
gh pr view 123 --json title,body,commits,files,reviews,comments

# Create PR
gh pr create --title "Title" --body "$(cat <<'EOF'
## Summary
- Change 1

## Test plan
- [ ] Test A
EOF
)"

# Review PR
gh pr review 123 --approve
gh pr review 123 --request-changes --body "Feedback"
gh pr review 123 --comment --body "Comment"

# Comment on PR
gh pr comment 123 --body "Comment text"

# View PR comments (including review comments)
gh api repos/{owner}/{repo}/pulls/123/comments

# Merge PR
# Preferred — waits for checks + reviews, then merges via queue:
gh pr merge 123 --auto --squash
# Bypass merge queue (admin only):
gh pr merge 123 --squash --admin
# NOTE: --merge-queue flag does NOT exist in gh CLI

# Update PR
gh pr edit 123 --title "New title" --add-label "ready"

# PR diff and checks
gh pr diff 123
gh pr checks 123
```

## Check Filtering

```bash
# Filter checks by status (pipe to jq — do NOT use --jq with !=)
gh pr checks 123 --json name,state,link | jq '.[] | select(.state != "SUCCESS" and .state != "SKIPPED")'
gh pr checks 123 --json name,state | jq '[.[] | select(.state == "FAILURE")] | length'
```

## PR Reviews with Inline Comments (via API)

`gh pr review` does **NOT** support inline file-level comments. Use the REST API with a temp file.

> **Never pass nested JSON inline in shell commands.** Shell quoting will mangle nested arrays/objects. Always write the payload to a temp file and use `--input`.

```bash
# 1. Write review payload to temp file
cat > /tmp/review-payload.json <<'EOF'
{
  "event": "COMMENT",
  "body": "Overall review summary here.",
  "comments": [
    {
      "path": "terraform/modules/vpc/main.tf",
      "line": 42,
      "side": "RIGHT",
      "body": "This CIDR block overlaps with the staging VPC."
    }
  ]
}
EOF

# 2. Submit the review via API
gh api repos/{owner}/{repo}/pulls/123/reviews \
  --method POST --input /tmp/review-payload.json

# 3. Clean up
rm -f /tmp/review-payload.json
```

### Payload field reference

| Field | Required | Description |
|-------|----------|-------------|
| `event` | Yes | `APPROVE`, `REQUEST_CHANGES`, or `COMMENT` |
| `body` | No | Top-level review summary |
| `comments[]` | No | Array of inline comment objects |
| `comments[].path` | Yes | File path relative to repo root |
| `comments[].line` | Yes | Line number in the diff |
| `comments[].side` | Yes | `RIGHT` (new code) or `LEFT` (deleted code) |
| `comments[].body` | Yes | Comment text (supports Markdown) |
| `comments[].start_line` | No | First line of a multi-line comment |
| `comments[].start_side` | No | Side for `start_line` |

## Code Search

```bash
gh search code "pattern" --repo owner/repo
gh search code "function_name" --owner <org> --language python
gh search repos "query" --owner <org>
```

## File Contents (via API)

```bash
gh api repos/{owner}/{repo}/contents/{path} --jq '.content' | base64 -d
gh api repos/{owner}/{repo}/contents/{path}?ref=branch-name
```

## Commits and Branches

```bash
gh api repos/{owner}/{repo}/commits --jq '.[].sha'
gh api repos/{owner}/{repo}/commits?sha=branch-name&per_page=10
gh api repos/{owner}/{repo}/branches --jq '.[].name'
gh api repos/{owner}/{repo}/git/refs -f ref="refs/heads/new-branch" -f sha="base-sha"
```

## Releases

```bash
gh release list
gh release view v1.0.0
gh release view --latest
gh api repos/{owner}/{repo}/releases/tags/v1.0.0
```

## `--jq` Expression Rules

**NEVER use `--jq` with expressions containing `!=`.** zsh history expansion rewrites `!=` to `\!=` before `gh` receives it, causing jq parse errors. This happens even inside single quotes.

**Workaround:** Pipe to `jq` instead of using `--jq`:

```bash
# CORRECT — pipe to jq, zsh doesn't mangle the expression
gh pr checks 123 --json name,state | jq '.[] | select(.state != "SUCCESS")'

# WRONG — zsh rewrites != to \!= causing jq parse error
gh pr checks 123 --json name,state --jq '.[] | select(.state != "SUCCESS")'
```

For simple `--jq` expressions without `!=`, `--jq` is fine:

```bash
# OK — no != operator
gh pr view 123 --json title --jq '.title'
```

Always use single quotes around jq expressions to prevent shell interpretation of `$`, backticks, etc.

## Common Pitfalls

- **Auth mismatch**: If `gh` says "could not determine repo owner", run `ghswitch` or `gh auth switch --user <work-account>`.
- **Token scopes**: Work token has `gist`, `read:org`, `repo`. If an operation fails with 403, check scopes with `gh auth status`.

## Tips

- Add `--json field1,field2` to most commands for structured JSON output
- Add `--jq '.expression'` to filter JSON output
- Use `gh api` for any REST API endpoint not covered by built-in commands
- Default repo is inferred from the current git remote; use `--repo owner/repo` to override
- Pagination: `gh api --paginate` for full results
