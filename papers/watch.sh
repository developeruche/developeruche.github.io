#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Rebuild a paper every time its markdown or metadata is saved.
#
#   ./papers/watch.sh              watch every paper
#   ./papers/watch.sh <slug>       watch just one
#
# Polls mtimes (no fswatch/entr dependency). Ctrl-C to stop.
# Pair with a static server and open /papers/preview.html?slug=<slug>, or
# just run ./papers/dev.sh which starts both.
# ---------------------------------------------------------------------------
set -uo pipefail

PAPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ONLY="${1:-}"

slugs() {
  for d in "$PAPERS_DIR"/*/; do
    local s; s="$(basename "$d")"
    [ "$s" = "_lib" ] && continue
    [ -f "$d/paper.md" ] || continue
    [ -n "$ONLY" ] && [ "$s" != "$ONLY" ] && continue
    echo "$s"
  done
}

# One fingerprint per paper: mtimes of the two files that drive a rebuild.
fingerprint() {
  local d="$PAPERS_DIR/$1"
  local a b
  a="$(stat -f %m "$d/paper.md"  2>/dev/null || stat -c %Y "$d/paper.md"  2>/dev/null)"
  b="$(stat -f %m "$d/meta.json" 2>/dev/null || stat -c %Y "$d/meta.json" 2>/dev/null)"
  echo "$a:$b"
}

found="$(slugs)"
if [ -z "$found" ]; then
  echo "no papers found${ONLY:+ matching '$ONLY'} in $PAPERS_DIR" >&2
  exit 1
fi
echo "watching:"; echo "$found" | sed 's/^/  · /'
echo "Ctrl-C to stop"

declare -A last
first=1
while true; do
  while IFS= read -r s; do
    cur="$(fingerprint "$s")"
    if [ "${last[$s]:-}" != "$cur" ]; then
      [ "$first" = "0" ] && printf '\n[%s] %s changed — rebuilding…\n' "$(date +%H:%M:%S)" "$s"
      last[$s]="$cur"
      "$PAPERS_DIR/build.sh" "$s" || true
    fi
  done <<< "$found"
  first=0
  sleep 0.5
done
