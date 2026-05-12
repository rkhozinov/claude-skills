"""Archive stale claude session transcripts into per-project monthly tarballs."""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
import tarfile
from collections import defaultdict
from pathlib import Path

from .live_sessions import is_recently_modified

HOME = Path.home()
PROJECTS_DIR = HOME / ".claude" / "projects"
TODOS_DIR = HOME / ".claude" / "todos"
ARCHIVE_DIR = HOME / ".claude" / "archive"


def project_root(jsonl: Path) -> Path:
    """Top-level project dir under PROJECTS_DIR for any nested transcript."""
    rel = jsonl.relative_to(PROJECTS_DIR)
    return PROJECTS_DIR / rel.parts[0]


def session_uuid(jsonl: Path) -> str:
    """Extract session UUID.

    Top-level transcript: PROJECTS_DIR/<slug>/<uuid>.jsonl  → stem
    Subagent transcript:  PROJECTS_DIR/<slug>/<uuid>/subagents/agent-*.jsonl
                          → parent.parent.name
    """
    if jsonl.parent.name == "subagents":
        return jsonl.parent.parent.name
    return jsonl.stem


def find_candidates(days: int) -> list[Path]:
    cutoff = dt.datetime.now().timestamp() - days * 86400
    out: list[Path] = []
    for jsonl in PROJECTS_DIR.rglob("*.jsonl"):
        try:
            if jsonl.stat().st_mtime >= cutoff:
                continue
        except FileNotFoundError:
            continue
        if is_recently_modified(jsonl):
            continue
        out.append(jsonl)
    return out


def group_by_project_month(files: list[Path]) -> dict[tuple[str, str], list[Path]]:
    groups: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for f in files:
        project = project_root(f).name
        month = dt.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m")
        groups[(project, month)].append(f)
    return groups


def archive_target(project: str, month: str) -> Path:
    return ARCHIVE_DIR / month / f"{project}.tar.gz"


def human_mb(n: int) -> str:
    return f"{n / 1048576:.1f} MB"


def short(s: str, width: int) -> str:
    return s if len(s) <= width else "…" + s[-(width - 1):]


def print_plan(groups: dict[tuple[str, str], list[Path]]) -> int:
    total_files = 0
    total_bytes = 0
    print(f"\n{'PROJECT':<70} {'MONTH':<8} {'FILES':>6} {'SIZE':>10}  TARGET")
    print("-" * 140)
    for (project, month), files in sorted(groups.items()):
        size = sum(f.stat().st_size for f in files)
        target = archive_target(project, month)
        try:
            rel = f"~/{target.relative_to(HOME)}"
        except ValueError:
            rel = str(target)
        print(f"{short(project, 70):<70} {month:<8} {len(files):>6} {human_mb(size):>10}  {rel}")
        total_files += len(files)
        total_bytes += size
    print("-" * 140)
    print(f"TOTAL: {total_files} files, {human_mb(total_bytes)} across {len(groups)} archives\n")
    return total_bytes


def make_archive(project: str, month: str, files: list[Path]) -> Path:
    """Create or merge tar.gz. arcname = path relative to project root, so
    restore preserves `<uuid>/subagents/agent-*.jsonl` layout."""
    target = archive_target(project, month)
    target.parent.mkdir(parents=True, exist_ok=True)
    proj_root = PROJECTS_DIR / project

    if target.exists():
        tmp_dir = target.parent / f".merge-{project}"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir()
        try:
            with tarfile.open(target, "r:gz") as tf:
                tf.extractall(tmp_dir)
            for f in files:
                arc = f.relative_to(proj_root)
                dst = tmp_dir / arc
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
            with tarfile.open(target, "w:gz") as tf:
                for sub in sorted(tmp_dir.rglob("*")):
                    if sub.is_file():
                        tf.add(sub, arcname=str(sub.relative_to(tmp_dir)))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        with tarfile.open(target, "w:gz") as tf:
            for f in files:
                tf.add(f, arcname=str(f.relative_to(proj_root)))

    return target


def verify_archive(target: Path, expected_arcnames: set[str]) -> bool:
    try:
        with tarfile.open(target, "r:gz") as tf:
            names = set(tf.getnames())
    except (tarfile.TarError, FileNotFoundError):
        return False
    return expected_arcnames.issubset(names)


def delete_orphan_todos(archived_uuids: set[str]) -> tuple[int, int]:
    if not TODOS_DIR.exists():
        return 0, 0
    deleted = 0
    bytes_freed = 0
    for todo in TODOS_DIR.glob("*.json"):
        stem = todo.stem
        sid = stem.split("-agent-", 1)[0] if "-agent-" in stem else stem
        if sid in archived_uuids:
            try:
                bytes_freed += todo.stat().st_size
                todo.unlink()
                deleted += 1
            except OSError:
                pass
    return deleted, bytes_freed


def confirm() -> bool:
    try:
        ans = input("Proceed? [y/N] ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


def restore(archive_path: Path) -> int:
    if not archive_path.exists():
        print(f"Archive not found: {archive_path}")
        return 1
    project = archive_path.stem.removesuffix(".tar")
    target = PROJECTS_DIR / project
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tf:
        tf.extractall(target)
    print(f"Restored {archive_path.name} → {target}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="archive-sessions")
    p.add_argument("--days", type=int, default=30, help="age threshold (default 30)")
    p.add_argument("--yes", action="store_true", help="skip confirmation")
    p.add_argument("--dry-run", action="store_true", help="preview only")
    p.add_argument("--restore", type=Path, help="restore an archive tarball")
    args = p.parse_args()

    if args.restore:
        return restore(args.restore)

    if not PROJECTS_DIR.exists():
        print(f"No projects dir: {PROJECTS_DIR}")
        return 0

    print(f"Scanning {PROJECTS_DIR} (>{args.days} days, excluding recently modified)...")

    candidates = find_candidates(args.days)
    if not candidates:
        print("No stale transcripts found.")
        return 0

    groups = group_by_project_month(candidates)
    total_bytes = print_plan(groups)

    if args.dry_run:
        print("Dry-run: no changes made.")
        return 0

    if not args.yes and not confirm():
        print("Aborted.")
        return 0

    archived_uuids: set[str] = set()
    bytes_freed = 0
    archives_made: list[Path] = []

    for (project, month), files in sorted(groups.items()):
        proj_root = PROJECTS_DIR / project
        expected = {str(f.relative_to(proj_root)) for f in files}
        target = make_archive(project, month, files)
        if not verify_archive(target, expected):
            print(f"  ✗ verify FAILED for {target} — sources kept")
            continue
        for f in files:
            try:
                bytes_freed += f.stat().st_size
                f.unlink()
                archived_uuids.add(session_uuid(f))
            except OSError as e:
                print(f"  ! could not delete {f}: {e}")
        archives_made.append(target)
        print(f"  ✓ {short(project, 60)} [{month}] → {target.name} ({len(files)} files)")

    todos_deleted, todos_bytes = delete_orphan_todos(archived_uuids)

    print()
    print(f"Archives: {len(archives_made)}")
    print(f"Transcripts removed: {len(archived_uuids)} unique sessions ({human_mb(bytes_freed)})")
    print(f"Orphan todos removed: {todos_deleted} ({human_mb(todos_bytes)})")
    print(f"Total reclaimed: {human_mb(bytes_freed + todos_bytes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
