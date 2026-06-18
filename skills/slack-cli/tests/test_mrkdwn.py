#!/usr/bin/env python3
"""Unit tests for slack-cli's markdown_to_mrkdwn + looks_like_markdown.

The CLI is a PEP-723 single-file script (not importable), so we ast-extract the
two pure functions and exec them in an isolated namespace.

Run: python3 skills/slack-cli/tests/test_mrkdwn.py
"""
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLACK = os.path.join(HERE, "..", "bin", "slack")


def load(*names):
    src = open(SLACK, encoding="utf-8").read()
    tree = ast.parse(src)
    # module-level constants the functions close over (e.g. _MD_LINK = re.compile(...))
    consts = [n for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id.startswith("_MD")
                      for t in n.targets)]
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    ns = {"re": re}
    exec(compile(ast.Module(consts + fns, []), "<x>", "exec"), ns)
    return tuple(ns[n] for n in names)


f, looks = load("markdown_to_mrkdwn", "looks_like_markdown")

CASES = [
    # (name, input, expected)
    ("bold", "**hi**", "*hi*"),
    ("bold-underscore", "__hi__", "*hi*"),
    ("italic", "*hi*", "_hi_"),
    ("bold-italic", "***hot***", "*_hot_*"),
    ("strike", "~~no~~", "~no~"),
    ("heading", "# Title", "*Title*"),
    ("link-basic", "[<prefix>-531](https://linear.app/x/<prefix>-531)",
     "<https://linear.app/x/<prefix>-531|<prefix>-531>"),
    ("link-paren-in-url", "[wiki](https://en.wikipedia.org/wiki/Foo_(bar))",
     "<https://en.wikipedia.org/wiki/Foo_(bar)|wiki>"),
    ("link-pipe-in-url", "[g](https://g.net/d?expr=a|b|c)",
     "<https://g.net/d?expr=a%7Cb%7Cc|g>"),
    ("link-angle-wrapped", "[x](<https://e.com/p>)", "<https://e.com/p|x>"),
    ("bullet-dash", "- one\n- two", "• one\n• two"),
    ("bullet-plus", "+ a\n+ b", "• a\n• b"),
    ("code-span-protected", "use `**not bold**` here", "use `**not bold**` here"),
    ("fence-protected", "```\n**x**\n```", "```\n**x**\n```"),
    ("empty", "", ""),
]


def run():
    fails = 0
    for name, src, exp in CASES:
        got = f(src)
        ok = got == exp
        fails += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            print(f"        in : {src!r}\n        exp: {exp!r}\n        got: {got!r}")

    # looks_like_markdown detector
    det = [
        ("**b**", True),
        ("[a](http://x)", True),
        ("# h", True),
        ("__b__", True),
        ("plain *slack* text", False),       # single-star is valid mrkdwn, not flagged
        ("`**code**`", False),               # code span stripped before probe
        ("just words", False),
    ]
    for src, want in det:
        got = bool(looks(src))
        ok = got == want
        fails += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] detect {src!r} -> {got} (want {want})")

    print(f"\n{'PASS' if not fails else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
