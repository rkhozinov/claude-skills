"""Detect transcripts of live claude sessions.

Claude does NOT hold .jsonl files open — it appends and closes per turn — so
`lsof` returns nothing useful. Instead, we treat any transcript modified
within `RECENT_SECONDS` as live. Combined with a `--days N` (>=1) age filter
this is overkill, but it protects against `--days 0` and clock skew.
"""

from __future__ import annotations

import time
from pathlib import Path

RECENT_SECONDS = 600  # 10 minutes


def is_recently_modified(path: Path, now: float | None = None) -> bool:
    now = now or time.time()
    try:
        return (now - path.stat().st_mtime) < RECENT_SECONDS
    except FileNotFoundError:
        return False
