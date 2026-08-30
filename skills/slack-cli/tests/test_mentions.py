#!/usr/bin/env python3
"""Unit tests for slack-cli's resolve_outbound_mentions.

Regression suite for the 2026-08-30 incident: `@Mohamed Esam` resolved via the
single-token regex to whoever owned the bare name "Mohamed" (Mohamed Tork,
display name "Torkey") instead of Mohamed Esam, and posted the wrong ping to a
shared channel. Three compounding causes, each covered here:

  1. The outbound regex captured only ONE name word, so a full name like
     `@Mohamed Esam` resolved as the bare first name plus dangling surname text.
     -> fix: greedy longest-phrase matching (longest candidate first, up to 5 words)
  2. A bare first name exact-matched a user whose real_name IS one word
     ("mohamed"), silently. -> fix: refuse single-word matches whose word also
     starts a longer name; warn and leave literal.
  3. Nothing warned — the mis-ping went out silently.

The CLI is a PEP-723 script (not importable), so we ast-extract the function
plus its module-level constants and exec into an isolated namespace with a
fixture user map — no network, no disk cache.

Run: python3 skills/slack-cli/tests/test_mentions.py
"""
import ast
import io
import os
import re
import sys
from contextlib import redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
SLACK = os.path.join(HERE, "..", "bin", "slack")


def load():
    src = open(SLACK, encoding="utf-8").read()
    tree = ast.parse(src)
    # resolve_outbound_mentions + its helpers, plus the module constants they read
    wanted_fns = {"resolve_outbound_mentions", "_rebuild_name_prefixes"}
    wanted_consts = {"_BROADCAST", "_OUT_TOKEN", "_OUT_TOKRE", "_OUT_MENTION",
                     "_FIRSTNAME_COLLISIONS"}
    def const_node(n):
        if isinstance(n, ast.Assign):
            return n.targets if isinstance(n, ast.Assign) else []
        if isinstance(n, ast.AnnAssign):
            return [n.target]
        return []
    nodes = []
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in wanted_fns:
            nodes.append(n)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            if any(isinstance(t, ast.Name) and t.id in wanted_consts for t in const_node(n)):
                nodes.append(n)
    ns = {
        "re": re, "sys": sys,
        "RESOLVE": True,
        "ensure_users_loaded": lambda: None,   # no network / disk cache in tests
        "USER_BY_NAME": {
            # distilled from the real wakecap workspace, 2026-08-30
            "mtork": "U03A42WH32P",           # real_name is literally "Mohamed"
            "mohamed": "U03A42WH32P",         # ...so this bare token indexed him
            "mohamed esam": "U0684HXGE3E",
            "mohamed.elsamy": "U025XSN4KQA",
            "mohamed farag": "U8EFR6AKE",
            "mohamed samir": "U094FMZQVTJ",
            "mohamed elsoly": "U025XSN4KQA",
            "mohamed tork": "U03A42WH32P",
            "ruslan": "U000RUS",              # single-name user, no collisions
            "ahmed": "U000AHMED",             # bare token, but no longer-name collision
        },
    }
    exec(compile(ast.Module(nodes, []), "<x>", "exec"), ns)
    ns["_rebuild_name_prefixes"]()  # function reads ns["USER_BY_NAME"] via its globals
    return ns["resolve_outbound_mentions"], ns


fix, ns = load()
COLL = ns["_FIRSTNAME_COLLISIONS"]

# Expected global side effect of the fixture map.
if "mohamed" not in ns["_FIRSTNAME_COLLISIONS"]:
    print("FAIL: _rebuild_name_prefixes did not flag 'mohamed' as a prefix-collision word")
    sys.exit(1)


def run() -> int:
    fails = 0

    def check(name, src, want, want_warn=False):
        nonlocal fails
        err = io.StringIO()
        with redirect_stderr(err):
            got = fix(src)
        warned = "warning:" in err.getvalue()
        ok = got == want and (warned == want_warn)
        fails += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            print(f"        in : {src!r}\n        exp: {want!r} (warn={want_warn})\n"
                  f"        got: {got!r} (warn={warned})\n"
                  f"        stderr: {err.getvalue()!r}")

    # --- the incident itself -------------------------------------------------
    # Full name must resolve as ONE mention to the RIGHT Mohamed.
    check("regression: '@Mohamed Esam' resolves the full name",
          "thanks @Mohamed Esam you're good",
          "thanks <@U0684HXGE3E> you're good")
    check("regression: quoted full name",
          'ping @"Mohamed Esam"', "ping <@U0684HXGE3E>")
    check("regression: bare '@Mohamed' is ambiguous (11+ Mohameds) and must NOT ping",
          "hi @Mohamed", "hi @Mohamed", want_warn=True)

    # --- longest-phrase mechanics --------------------------------------------
    check("longest wins even when bare token also indexes someone",
          "assign to @Mohamed Esam and @Mohamed Farag",
          "assign to <@U0684HXGE3E> and <@U8EFR6AKE>")
    check("bare handle beats longer names",
          "@mtork please check", "<@U03A42WH32P> please check")
    check("trailing punctuation stays outside the mention",
          "@Mohamed Esam, ship it", "<@U0684HXGE3E>, ship it")
    check("text after the full name is preserved verbatim",
          "@Mohamed Esam is on it", "<@U0684HXGE3E> is on it")
    check("bare token WITHOUT collision still pings + keeps tail",
          "cc @Ahmed now", "cc <@U000AHMED> now")
    check("bare token NOT in map at all: literal + warning",
          "cc @Zbigniew today", "cc @Zbigniew today", want_warn=True)
    check("unknown full name: literal + warning",
          "ask @Zbigniew Nowak", "ask @Zbigniew Nowak", want_warn=True)

    # --- broadcast mentions survive the rewrite -------------------------------
    check("@here alone -> broadcast", "@here", "<!here>")
    check("@here with prose -> broadcast + tail", "@here deploy is stuck",
          "<!here> deploy is stuck")
    check("@channel -> broadcast", "@channel note:", "<!channel> note:")

    # --- protections ----------------------------------------------------------
    check("code span is protected", "ping `@Mohamed Esam`", "ping `@Mohamed Esam`")
    check("fenced code is protected", "```\n@Mohamed Esam\n```", "```\n@Mohamed Esam\n```")
    check("email-like @ never resolves", "mail a@b.com please", "mail a@b.com please")
    check("mid-name @ in URL path never resolves", "see https://x.com/@Mohamed/Esam",
          "see https://x.com/@Mohamed/Esam")

    # RESOLVE=False short-circuit (function reads module global RESOLVE)
    ns["RESOLVE"] = False
    got = fix("@Mohamed Esam @mtork")
    ok = got == "@Mohamed Esam @mtork"
    fails += not ok
    print(f"  [{'ok' if ok else 'FAIL'}] RESOLVE=False leaves text raw")
    if not ok:
        print(f"        got: {got!r}")
    ns["RESOLVE"] = True

    print(f"\n{'PASS' if not fails else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())