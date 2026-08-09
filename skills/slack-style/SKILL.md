---
name: slack-style
description: Build or refresh the personal Slack voice profile from the user's own real messages — scrape and label their writing, report the evidence, and distill it into ~/.claude/slack-voice/voice.md, which slack-cli then uses when drafting messages. Use when the user wants Slack replies written in their own voice, asks to build/refresh/rebuild their Slack style, or complains that agent-written Slack messages are too long or do not sound like them.
---

# Slack style builder

Produces `~/.claude/slack-voice/voice.md`: a distilled profile of how the user
actually writes in Slack, plus a bank of their real messages to imitate.
`slack-cli` reads that file before every `send`/`reply`.

## Why this exists

Agent-written Slack messages are ~100x longer than what the user types by hand,
and they read like a report rather than a colleague. Relaying LLM output verbatim
pushes work onto the reader and reads as unprofessional
([nomeatproxy.com](https://nomeatproxy.com/)). The honest fix is to read, verify,
and answer in your own words. This skill keeps the verification and automates the
"own words" part, by learning the words from the user's own history.

## Run it

```bash
slack style scrape --since 180d        # fetch + label; incremental, safe to re-run
slack style stats                      # evidence report (also written to stats.md)
slack style exemplars -n 200           # best hand-typed messages, with context
```

`scrape` takes a few minutes on a first run (paged search + one
`conversations.replies`/`history` call per thread/channel, with 429 backoff).
Re-runs skip everything already in the corpus. `--full` rebuilds from scratch.

## How the labeling works

Exact, not guessed. Slack tags every message posted through the Web API with
`app_id`/`bot_id`; a message typed in a Slack client has `client_msg_id` and
neither. So `provenance: human` is genuinely the user's own writing and
`provenance: app` is everything an agent posted as them. `search.messages` does
not return those fields — only `conversations.history`/`replies` do — which is
why the scrape does two passes.

**One blind spot:** text *pasted* from an agent into the Slack client is posted by
the client, so it labels as `human`. These are easy to spot in the exemplar dump —
they carry the formatting tells (bullet lists, bold section headers, "Everything is
already set up correctly") that the rest of the corpus never uses. Hand-pick past
them when writing the exemplar section; do not just take the top N.

## Then write the profile

Read `slack style exemplars -n 200` output and `stats.md`, then write
`~/.claude/slack-voice/voice.md` with these sections:

1. **Register** — what the user's real messages do: capitalization, contractions,
   recurring openers and closers, emoji habits, how they address people, how they
   say "I'm on it" / "that's done" / "I was wrong". Quote the actual words.
2. **Length** — the measured median and p90 from `stats.md`, stated as the target.
3. **Escape hatch** — what to do when detail is genuinely needed: verdict in the
   message, detail in a thread reply or behind a link, and say what was left out.
   State explicitly that the link must be something the *recipient* can open — a PR,
   a dashboard, a shared doc, a Slack file upload — and that a path on the sender's
   own machine (`~/…`, `/tmp/…`) is never an acceptable pointer. An agent drafting
   a message knows its own filesystem and will reach for it otherwise.
4. **Anti-patterns** — drawn from the `app` bucket, which is a ready-made list of
   tells: em dashes, `*Bold lead-in.*` openers, bullet walls, stacked "two things"
   structure, unprompted jargon.
5. **Exemplars** — 15–25 verbatim messages grouped by intent (ack, on-it, status,
   unblock-confirm, ask, correction, defer, escalate), each with the message it
   was answering. This section does the real work; rules alone do not reproduce a
   voice.

Re-run the whole thing when the profile drifts or after a few months of new history.

## Privacy — read before touching git

The corpus is real conversations with real colleagues, and this repo is public.

- Everything the builder writes lives in `~/.claude/slack-voice/`
  (`corpus.jsonl`, `state.json`, `stats.md`, `voice.md`). **Never** copy any of it
  into this repo, a commit message, a PR body, or an issue.
- Ship only code and instructions here. If an example is needed, invent one.
- `SLACK_VOICE_DIR` overrides the location (used by the tests).
