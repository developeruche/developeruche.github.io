#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# One command for the live paper-writing loop: static server + watcher.
#
#   ./papers/dev.sh                 serve on :8000, watch every paper
#   ./papers/dev.sh <slug>          watch just one paper
#   PORT=9000 ./papers/dev.sh       serve on another port
#
# Then edit papers/<slug>/paper.md and watch the preview refresh.
# Ctrl-C stops both.
# ---------------------------------------------------------------------------
set -uo pipefail

PAPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$PAPERS_DIR")"
PORT="${PORT:-8000}"
SLUG="${1:-}"
SERVER_PID=""

cleanup() { [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null; exit 0; }
trap cleanup INT TERM

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "• port $PORT already serving — reusing it"
else
  ( cd "$ROOT" && python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 ) &
  SERVER_PID=$!
  echo "• static server started on :$PORT"
fi

if [ -n "$SLUG" ]; then
  echo "• preview:     http://localhost:$PORT/papers/preview.html?slug=$SLUG"
  echo "• public page: http://localhost:$PORT/publications/$SLUG/"
else
  echo "• preview:     http://localhost:$PORT/papers/preview.html"
  echo "• publications: http://localhost:$PORT/publications.html"
fi
echo

"$PAPERS_DIR/watch.sh" ${SLUG:+"$SLUG"}
