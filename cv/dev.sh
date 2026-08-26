#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# One command for the live-editing loop: static server + LaTeX watcher.
#
#   ./cv/dev.sh            serve on :8000
#   PORT=9000 ./cv/dev.sh  serve on another port
#
# Then edit cv/cv.tex and watch http://localhost:8000/cv/preview.html refresh.
# Ctrl-C stops both.
# ---------------------------------------------------------------------------
set -uo pipefail

CV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$CV_DIR")"
PORT="${PORT:-8000}"
SERVER_PID=""

cleanup() {
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "• port $PORT already serving — reusing it"
else
  ( cd "$ROOT" && python3 serve.py "$PORT" >/dev/null 2>&1 ) &
  SERVER_PID=$!
  echo "• static server started on :$PORT"
fi

echo "• preview:  http://localhost:$PORT/cv/preview.html"
echo "• download: http://localhost:$PORT/cv/"
echo

"$CV_DIR/watch.sh"
