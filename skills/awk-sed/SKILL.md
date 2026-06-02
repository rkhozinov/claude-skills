---
name: awk-sed
description: Reference for awk and sed one-liners. Use when transforming text streams in shell pipelines where Read/Edit/Grep are unsuitable — log slicing, multi-line stream edits, column math, CSV/TSV reshaping. Prefer Edit tool for file rewrites; this skill is for pipe-stage transforms.
---

# awk + sed reference

## When to use
- Log slicing in pipelines: `kubectl logs ... | awk ...`
- CSV/TSV column ops (sum, filter, reshape) without pulling whole file into memory
- Multi-line stream rewrites mid-pipeline
- One-off stdin transforms where writing a temp file + Edit is overkill

## When NOT to use
- File rewrites on disk → use Edit tool
- Searching code → use Grep (ripgrep) or ast-grep
- Counting matches → `rg -c`

## sed cheat
- Replace first per line: `sed 's/old/new/'`
- Replace all: `sed 's/old/new/g'`
- In-place (BSD/macOS): `sed -i '' 's/old/new/g' file`
- In-place (GNU): `sed -i 's/old/new/g' file`
- Delete matching lines: `sed '/pattern/d'`
- Keep only matching lines: `sed -n '/pattern/p'`
- Print line range: `sed -n '10,20p'`
- Multi-expression: `sed -e 's/a/b/' -e 's/c/d/'`
- Extended regex + capture: `sed -E 's/([0-9]+)ms/\1/'`
- Insert before match: `sed '/pattern/i\
NEW LINE'`
- Append after match: `sed '/pattern/a\
NEW LINE'`

## awk cheat
- Print column: `awk '{print $2}'`
- Custom delim: `awk -F, '{print $3}'`
- Multi-delim: `awk -F'[,;]' '{print $2}'`
- Sum column: `awk '{s+=$1} END{print s}'`
- Average: `awk '{s+=$1; n++} END{print s/n}'`
- Filter rows: `awk '$3 > 100'`
- Filter + print: `awk '$3 > 100 {print $1, $3}'`
- NR (line num), NF (field count), $0 (whole line), $NF (last field)
- Print last field: `awk '{print $NF}'`
- Unique by column: `awk '!seen[$1]++'`
- Group count: `awk '{c[$1]++} END{for(k in c) print k, c[k]}'`
- Join fields with custom OFS: `awk 'BEGIN{OFS=","} {print $1,$3}'`
- Range between markers: `awk '/START/,/END/'`
- CSV with quoted fields → use `csvkit`/`xsv`/`qsv`, not awk

## Common compositions
- Top memory hogs: `ps aux | awk '{print $4, $11}' | sort -nr | head`
- Tail uniq log lines: `tail -f log | awk '!seen[$0]++'`
- Sum file sizes from `ls -l`: `ls -l | awk 'NR>1 {s+=$5} END{print s}'`
- HTTP 5xx grep + count by path: `awk '$9 ~ /^5/ {c[$7]++} END{for(p in c) print c[p], p}' access.log | sort -nr`
- Strip ANSI color codes: `sed -E 's/\x1B\[[0-9;]*[mK]//g'`
- Squeeze multiple blank lines: `sed '/^$/N;/^\n$/D'`

## Gotchas
- macOS BSD `sed` ≠ GNU `sed`. `-i` needs `''` arg on macOS. Use `gsed` (`brew install gnu-sed`) for portability.
- awk uses 1-based field indexing.
- Quote shell vars into awk: `awk -v x="$VAR" '{print x, $1}'` (NEVER interpolate raw — quoting bugs + injection).
- `sed -E` for ERE on both BSD/GNU; avoid GNU-only `\<` `\>` word boundaries.
- awk's `print` adds OFS between args; concatenation with no comma joins without separator.

## Decision tree
- Want structural code change? → ast-grep
- Want to find text in code? → Grep tool (ripgrep)
- Want to rewrite file on disk? → Edit tool
- Want to transform stdin/pipeline? → this skill (awk or sed)
- Want column math / aggregation? → awk
- Want pattern-based line edit? → sed
