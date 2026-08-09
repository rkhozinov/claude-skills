#!/usr/bin/env python3
"""Unit tests for slack-cli's `provenance` + `_emit` message labeling.

This is the branch the whole voice profile rests on: mislabel one message and
agent-written text leaks into the corpus of "what I sound like". Same
ast-extraction trick as test_mrkdwn.py — the CLI is a PEP-723 script, not
importable.

Run: python3 skills/slack-cli/tests/test_provenance.py
"""
import ast
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLACK = os.path.join(HERE, "..", "bin", "slack")


def load(*names):
    src = open(SLACK, encoding="utf-8").read()
    tree = ast.parse(src)
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    ns = {"json": json}
    exec(compile(ast.Module(fns, []), "<x>", "exec"), ns)
    return tuple(ns[n] for n in names)


ME = "U000SELF"

# Shapes seen in real conversations.history output.
TYPED = {"user": ME, "ts": "100.000100", "text": "lemme take a look",
         "client_msg_id": "abc-123"}
VIA_CLI = {"user": ME, "ts": "200.000200", "text": "The deploy is stuck and nothing reached prod.",
           "app_id": "A00000000", "bot_id": "B00000000"}
VIA_OTHER_APP = {"user": ME, "ts": "300.000300", "text": "posted by a workflow",
                 "app_id": "A99999999"}
BOT_ONLY = {"user": ME, "ts": "400.000400", "text": "bot_id but no app_id",
            "bot_id": "B11111111"}


def run() -> int:
    provenance, _emit = load("provenance", "_emit")
    fails = 0

    for msg, want in [(TYPED, "human"), (VIA_CLI, "app"), (VIA_OTHER_APP, "app"), (BOT_ONLY, "app")]:
        got = provenance(msg)
        ok = got == want
        fails += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {msg['text'][:32]!r} -> {got} (want {want})")

    # _emit: only my messages, no subtypes, no empties; context comes from the
    # neighbouring messages written by someone else.
    unit = [
        {"user": "U000THEM", "ts": "99.000000", "text": "can you have a look?"},
        TYPED,
        {"user": ME, "ts": "101.000000", "text": "", "client_msg_id": "d"},          # empty
        {"user": ME, "ts": "102.000000", "text": "joined", "subtype": "channel_join"},  # system
        {"user": "U000THEM", "ts": "160.000000", "text": "thanks! did it work?"},
        VIA_CLI,
    ]
    buf = io.StringIO()
    seen: set = set()
    n = _emit(unit, ME, seen, "C000CHAN", "channel", buf)
    recs = [json.loads(x) for x in buf.getvalue().splitlines()]

    checks = [
        ("emitted 2 records", n == 2 and len(recs) == 2),
        ("skipped empty + system", {r["ts"] for r in recs} == {"100.000100", "200.000200"}),
        ("labels split", [r["provenance"] for r in recs] == ["human", "app"]),
        ("prompt = their prior msg", recs[0]["prompt"] == "can you have a look?"),
        ("next = their reply", recs[0]["next"] == "thanks! did it work?"),
        ("follow-up question flagged", recs[0]["next_is_question"] is True),
        ("latency measured", recs[0]["reply_latency_s"] == 60),
        ("no reply -> null latency", recs[1]["reply_latency_s"] is None),
        ("chars counted", recs[0]["chars"] == len(TYPED["text"])),
    ]
    for label, ok in checks:
        fails += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {label}")

    # Re-running over the same unit must not duplicate (incremental scrape).
    buf2 = io.StringIO()
    again = _emit(unit, ME, seen, "C000CHAN", "channel", buf2)
    ok = again == 0
    fails += not ok
    print(f"  [{'ok' if ok else 'FAIL'}] rescrape is idempotent (wrote {again})")

    print(f"\n{'PASS' if not fails else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
