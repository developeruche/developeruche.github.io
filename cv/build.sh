#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Compile cv.tex -> assets/cv/nwele-uchenna-david-cv.pdf
#
#   ./cv/build.sh          compile once, print result
#   ./cv/build.sh --quiet  same, but only speak up on failure
#
# Aux files (.aux/.log/.out) stay in cv/.build/ so the repo stays clean.
# On a failed compile the previously published PDF is left untouched, so the
# live /cv route never serves a broken or half-written file.
# ---------------------------------------------------------------------------
set -uo pipefail

CV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$CV_DIR")"
BUILD_DIR="$CV_DIR/.build"
STATUS="$CV_DIR/.build-status.json"
OUT="$ROOT/assets/cv/nwele-uchenna-david-cv.pdf"
QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1

# Homebrew's texlive lives here and may not be on a non-interactive PATH.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v pdflatex >/dev/null 2>&1; then
  echo "error: pdflatex not found. Install it with:  brew install texlive" >&2
  exit 127
fi

mkdir -p "$BUILD_DIR" "$(dirname "$OUT")"

# TeX wraps log lines at 79 cols by default, which splits an error across two
# lines and leaves the grep below with a bare "cv.tex:213:" and no message.
export max_print_line=10000
export error_line=254
export half_error_line=238

# Two passes: hyperref resolves its link targets on the second run.
# Run from CV_DIR with a relative filename so errors read "cv.tex:213: ..."
# rather than carrying an absolute path that crowds out the message.
run_pass() {
  ( cd "$CV_DIR" && pdflatex -interaction=nonstopmode -file-line-error \
      -output-directory=".build" "cv.tex" >/dev/null 2>&1 )
}

run_pass
run_pass
LOG="$BUILD_DIR/cv.log"

# pdflatex's exit code is unreliable under nonstopmode; trust the artifact
# plus the log instead.
ERRORS=""
[ -f "$LOG" ] && ERRORS="$(grep -E '^(\./)?.*\.tex:[0-9]+:|^! ' "$LOG" | cut -c1-300 | head -40)"

write_status() { # $1=ok|error  $2=message
  python3 - "$1" "$2" "$STATUS" <<'PY'
import json, sys, time
ok, msg, path = sys.argv[1] == "ok", sys.argv[2], sys.argv[3]
json.dump({"ok": ok, "time": time.time(), "log": msg}, open(path, "w"))
PY
}

if [ -f "$BUILD_DIR/cv.pdf" ] && [ -z "$ERRORS" ]; then
  cp "$BUILD_DIR/cv.pdf" "$OUT"
  # Join lines before matching: the summary is wrapped in any log written
  # before max_print_line above took effect.
  # -a: joining the log can leave bytes that make grep treat it as binary.
  PAGES="$(LC_ALL=C tr -d '\n' < "$LOG" | LC_ALL=C grep -aoE '\([0-9]+ pages?,' | head -1 | tr -d '(,')"
  write_status ok ""
  [ "$QUIET" -eq 1 ] || echo "✓ built $(basename "$OUT") (${PAGES:-? pages})"
  exit 0
fi

write_status error "${ERRORS:-Compile failed and no error line was captured. See $LOG}"
echo "✗ LaTeX build failed:" >&2
echo "${ERRORS:-  (no error lines captured — see $LOG)}" >&2
exit 1
