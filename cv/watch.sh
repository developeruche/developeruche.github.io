#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Rebuild the CV every time cv.tex is saved.
#
#   ./cv/watch.sh
#
# Polls the file's mtime (no fswatch/entr dependency). Ctrl-C to stop.
# Pair it with a static server and open /cv/preview.html to see the PDF
# refresh on its own — or just run ./cv/dev.sh, which starts both.
# ---------------------------------------------------------------------------
set -uo pipefail

CV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEX="$CV_DIR/cv.tex"

mtime() { stat -f %m "$TEX" 2>/dev/null || stat -c %Y "$TEX" 2>/dev/null; }

echo "watching $(basename "$TEX") — Ctrl-C to stop"
last=""
while true; do
  cur="$(mtime)"
  if [ -n "$cur" ] && [ "$cur" != "$last" ]; then
    [ -n "$last" ] && printf '\n[%s] cv.tex changed — rebuilding…\n' "$(date +%H:%M:%S)"
    last="$cur"
    "$CV_DIR/build.sh" || true
  fi
  sleep 0.4
done
