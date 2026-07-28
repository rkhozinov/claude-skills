#!/usr/bin/env bash
# Re-vendor upstream skills pinned in vendor.json, re-apply local edits, leave the
# result staged in the worktree for `git diff` review. Never commits.
#
# Usage:  scripts/vendor-refresh.sh [source-name ...]     (default: all sources)
#         VENDOR_REF=main scripts/vendor-refresh.sh ponytail   (override the pin)

set -euo pipefail
cd "$(dirname "$0")/.."
REPO_ROOT=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

want=("$@")
wanted() { [ ${#want[@]} -eq 0 ] && return 0; for w in "${want[@]}"; do [ "$w" = "$1" ] && return 0; done; return 1; }

# ponytail: jq drives the loop instead of a bash JSON parser. It is a hard dep here anyway.
count=$(jq '.sources | length' vendor.json)
for i in $(seq 0 $((count - 1))); do
  name=$(jq -r ".sources[$i].name" vendor.json)
  wanted "$name" || continue
  repo=$(jq -r ".sources[$i].repo" vendor.json)
  ref=${VENDOR_REF:-$(jq -r ".sources[$i].ref" vendor.json)}
  license=$(jq -r ".sources[$i].license" vendor.json)

  echo "==> $name @ $ref"
  git clone -q --depth 1 --branch "$ref" "$repo" "$TMP/$name"
  sha=$(git -C "$TMP/$name" rev-parse HEAD)

  jq -r ".sources[$i].skills[]" vendor.json | while read -r skill; do
    rm -rf "skills/$skill"
    cp -r "$TMP/$name/skills/$skill" "skills/$skill"
  done
  jq -r ".sources[$i].prune[]" vendor.json | while read -r p; do
    rm -f "skills/$p"
  done
  [ -f "$TMP/$name/LICENSE" ] && cp "$TMP/$name/LICENSE" "$license"

  # Record what we actually pulled, so the pin never drifts from reality.
  tmpjson=$(mktemp)
  jq --arg s "$sha" --arg r "$ref" ".sources[$i].sha = \$s | .sources[$i].ref = \$r" vendor.json > "$tmpjson"
  mv "$tmpjson" vendor.json
  echo "    sha $sha"
done

# --- local edits, re-applied after every refresh -----------------------------
# Upstream cross-references skills this bundle does not ship. Left unpatched they
# dangle and the model chases a skill that is not there.
sd=skills/systematic-debugging/SKILL.md
if [ -f "$sd" ]; then
  perl -pi -e 's/`superpowers:test-driven-development`/`test-driven-development`/' "$sd"
  perl -pi -e 's/Use the `superpowers:verification-before-completion` skill before claiming success/Verify with a real command run and paste the output before claiming success/' "$sd"
fi
wgt=skills/test-driven-development/writing-good-tests.md
[ -f "$wgt" ] && perl -pi -e 's/ \(superpowers:writing-skills\)//' "$wgt"

# Upstream descriptions are keyword-stuffed to force auto-triggering; each one costs
# ~200 tokens of context in EVERY session. These skills are invoked deliberately, so
# a short description is enough.
python3 - <<'PY'
import re, pathlib
SHORT = {
    "skills/ponytail/SKILL.md":
        "Forces the laziest solution that actually works: YAGNI, stdlib before "
        "dependencies, one line before fifty. Use when asked for the minimal or "
        "simplest approach, or when complaining about over-engineering.",
}
for path, desc in SHORT.items():
    p = pathlib.Path(path)
    if not p.exists():
        continue
    t = p.read_text()
    m = re.match(r"(---\n)(.*?)(\n---)", t, re.S)
    if not m:
        continue
    fm = re.sub(r"^description:.*?(?=^\w+:|\Z)", f"description: {desc}\n",
                m.group(2), flags=re.S | re.M)
    p.write_text(t[:m.start(2)] + fm.rstrip("\n") + t[m.end(2):])
    print(f"    trimmed description: {path}")
PY

echo
echo "Done. Review with: git -C $REPO_ROOT diff"
