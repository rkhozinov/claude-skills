---
name: diff
description: Launch an external visual diff tool (Zed or PyCharm) to view git changes
user_invocable: true
---

# /diff — External Visual Diff Viewer

Open git diffs in an external visual diff tool.

## Usage

The user invokes `/diff` with optional arguments, or asks in natural language (e.g. "show me what changed", "show staged changes", "compare with main").

Parse the arguments to determine **what to diff** and **which tool** to use, then run the appropriate `git difftool` command.

### Argument parsing

| Argument | Meaning |
|---|---|
| *(none)* | unstaged changes (`git difftool -y`) |
| `staged` or `--staged` or `--cached` | staged changes (`git difftool -y --staged`) |
| `all` | all uncommitted changes — run **both** staged and unstaged difftool commands |
| `HEAD~N` or a commit ref | diff against that ref (`git difftool -y <ref>`) |
| a single branch name (e.g. `main`) | compare current HEAD with that branch (`git difftool -y <branch>`) |
| two branch names (e.g. `main feature`) | compare two branches (`git difftool -y <branch1> <branch2>`) |
| a file path | diff that specific file (`git difftool -y -- <path>`) |
| `--tool <name>` | override the diff tool (e.g. `--tool pycharm`) |

The `--tool <name>` flag can appear anywhere in the arguments and combines with any of the above.

### Natural language mapping

- "show me what changed" / "what's different" → unstaged changes
- "show staged changes" / "what's staged" → `--staged`
- "show all changes" / "all uncommitted" → `all`
- "compare with main" / "diff against main" → branch diff with `main`
- "use pycharm" / "open in pycharm" → `--tool pycharm`

## Execution steps

1. **Verify git repo**: Run `git rev-parse --is-inside-work-tree`. If it fails, tell the user they're not in a git repo and stop.

2. **Show summary first**: Run `git diff --stat` (or `git diff --staged --stat`, etc.) to show a text summary of what changed. If the stat output is empty, report "No changes found" and **do not launch the tool**.

3. **Launch the visual diff tool**: Run `git difftool -y [options]` using the Bash tool with `run_in_background: true` so it doesn't block the conversation. Always include `-y` to skip per-file prompts.

   - Default tool comes from git config (`diff.tool`, currently `zed`).
   - If `--tool <name>` was specified, add `-t <name>` to the command.

4. **Report**: Tell the user what tool was launched and what diff is being shown.

## Examples

```
# User: /diff
git diff --stat
git difftool -y

# User: /diff staged
git diff --staged --stat
git difftool -y --staged

# User: /diff all
git diff --stat
git diff --staged --stat
git difftool -y
git difftool -y --staged

# User: /diff src/main.py
git diff --stat -- src/main.py
git difftool -y -- src/main.py

# User: /diff main
git diff --stat main
git difftool -y main

# User: /diff main feature
git diff --stat main feature
git difftool -y main feature

# User: /diff HEAD~1
git diff --stat HEAD~1
git difftool -y HEAD~1

# User: /diff --tool pycharm
git diff --stat
git difftool -y -t pycharm

# User: /diff staged --tool pycharm
git diff --staged --stat
git difftool -y --staged -t pycharm
```
