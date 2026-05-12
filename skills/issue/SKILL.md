---
name: issue
description: Create Linear issues from plain language. Use whenever the user asks to create a ticket, issue, task, or bug in Linear — even if they just say "file a ticket for X" or "create an issue about Y". The user provides a natural language description; this skill handles title, team, priority, description, and all CLI syntax. MUST be invoked before ANY linear-cli issues create command.
user_invocable: true
---

# Create Linear Issue from Plain Language

The user describes what they want in plain language. You handle everything else.

## How It Works

1. User says something like: `/linear-issue create a ticket for removing duplicate appsettings files`
2. You parse the intent and generate:
   - A concise title (imperative, under 80 chars)
   - Team (default: `<team>` for infra work, infer from context otherwise)
   - Priority (infer from urgency/impact, default: 4 for housekeeping, 3 for normal, 2 for bugs)
   - State (default: `Backlog`)
   - A well-structured markdown description with Problem, Proposed Change, and Notes sections

## CLI Syntax Reminder

Title is a **POSITIONAL argument**. Not `--title`.

```bash
linear-cli issues create "The Title" \
  --team "<team>" \
  --priority 4 \
  --state "Backlog" \
  --description "$(cat <<'EOF'
## Problem
What's wrong or missing.

## Proposed Change
What to do about it.

## Notes
Additional context.
EOF
)"
```

## Team Selection

**CRITICAL — ignore "<org>" as a team name.** "<org>" is the company, not the infra team. The <org> team (`<prefix>`) exists in Linear but is NOT for infra/devops/k8s/terraform work. If the user types "<org> team" while the topic is infra-context, route to **<team>** instead and confirm only if ambiguous. Past mistake: created <prefix>-46 instead of <prefix>-355 — user explicitly forbade <org> team for infra tickets.

| Context | Team |
|---------|------|
| Infrastructure, Terraform, Kubernetes, CI/CD, DevOps, MQTT, services, deployments | **<team>** |
| IT operations, internal tools, accounts | IT |
| Other / unclear | Ask the user |

**Never use `<org>`/`<prefix>` for infra tickets, even if the user literally says "<org> team".** Confirm or override to `<team>`.

See the `linear-cli` skill for full team name-to-key mapping.

## Priority Selection

| Signal | Priority |
|--------|----------|
| Production down, blocking, urgent | 1 (urgent) |
| Bug, broken functionality, security | 2 (high) |
| Feature request, normal task | 3 (normal) |
| Housekeeping, refactor, cleanup, tech debt | 4 (low) |

## Workflow

1. Parse the user's plain language request
2. If context from the current conversation is relevant (error messages, file paths, service names), incorporate it into the description
3. Generate the `linear-cli issues create` command
4. Run it
5. Report the issue ID and URL

Do not ask the user to confirm parameters unless the team or priority is genuinely ambiguous. Just create the issue — the user can always update it later.
