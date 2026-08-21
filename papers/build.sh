#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Compile a paper:  papers/<slug>/paper.md  ->  assets/papers/<slug>.pdf
#
#   ./papers/build.sh <slug>      build one paper
#   ./papers/build.sh --all       build every paper under papers/
#   ./papers/build.sh <slug> -q   quiet unless it fails
#
# Pipeline: pandoc renders the markdown into LaTeX using _lib/paper.latex,
# then pdflatex runs twice (second pass resolves the ToC and hyperref links).
#
# Intermediates live in papers/<slug>/.build/ and are gitignored. A failed
# compile leaves the previously published PDF in place, so the live
# /publications/<slug>/ page never serves a broken or half-written file.
# ---------------------------------------------------------------------------
set -uo pipefail

PAPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$PAPERS_DIR")"
LIB="$PAPERS_DIR/_lib"

export PATH="/opt/homebrew/bin:/usr/local/bin:/opt/anaconda3/bin:$PATH"

for tool in pandoc pdflatex; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "error: $tool not found." >&2
    [ "$tool" = pdflatex ] && echo "  install with: brew install texlive" >&2
    [ "$tool" = pandoc ]   && echo "  install with: brew install pandoc" >&2
    exit 127
  }
done

# TeX wraps log lines at 79 cols, splitting an error away from its message.
export max_print_line=10000 error_line=254 half_error_line=238

write_status() { # $1=dir $2=ok|error $3=message
  python3 - "$2" "$3" "$1/.build-status.json" <<'PY'
import json, sys, time
ok, msg, path = sys.argv[1] == "ok", sys.argv[2], sys.argv[3]
json.dump({"ok": ok, "time": time.time(), "log": msg}, open(path, "w"))
PY
}

build_one() {
  local slug="$1" quiet="${2:-0}"
  local dir="$PAPERS_DIR/$slug"
  local build="$dir/.build"
  local out="$ROOT/assets/papers/$slug.pdf"

  [ -f "$dir/paper.md" ]  || { echo "error: $dir/paper.md not found"  >&2; return 1; }
  [ -f "$dir/meta.json" ] || { echo "error: $dir/meta.json not found" >&2; return 1; }

  mkdir -p "$build" "$(dirname "$out")"

  # --- markdown -> LaTeX -------------------------------------------------
  local perr
  perr="$(pandoc "$dir/paper.md" \
            --from=markdown+tex_math_dollars+pipe_tables+fenced_code_attributes \
            --to=latex \
            --standalone \
            --template="$LIB/paper.latex" \
            --metadata-file="$dir/meta.json" \
            --syntax-highlighting=pygments \
            --number-sections \
            --resource-path="$dir" \
            --output="$build/paper.tex" 2>&1)"
  if [ $? -ne 0 ]; then
    write_status "$dir" error "pandoc: $perr"
    echo "✗ [$slug] pandoc failed:" >&2; echo "$perr" >&2
    return 1
  fi

  # --- LaTeX -> PDF ------------------------------------------------------
  run_pass() {
    ( cd "$build" && pdflatex -interaction=nonstopmode -file-line-error \
        -output-directory=. paper.tex >/dev/null 2>&1 )
  }
  run_pass; run_pass

  local log="$build/paper.log" errors=""
  if [ -f "$log" ]; then
    errors="$(LC_ALL=C grep -aE '^(\./)?.*\.tex:[0-9]+:|^! ' "$log" | cut -c1-300 | head -40)"
    # The author writes markdown but LaTeX reports lines in the generated .tex,
    # so quote the offending source line — that text is findable in paper.md.
    if [ -n "$errors" ] && [ -f "$build/paper.tex" ]; then
      errors="$(printf '%s\n' "$errors" | python3 "$LIB/annotate_errors.py" "$build/paper.tex")"
    fi
  fi

  if [ -f "$build/paper.pdf" ] && [ -z "$errors" ]; then
    cp "$build/paper.pdf" "$out"
    local pages
    pages="$(LC_ALL=C tr -d '\n' < "$log" | LC_ALL=C grep -aoE '\([0-9]+ pages?,' | head -1 | tr -d '(,')"
    write_status "$dir" ok ""
    [ "$quiet" = "1" ] || echo "✓ [$slug] ${pages:-? pages} → assets/papers/$slug.pdf"
    return 0
  fi

  write_status "$dir" error "${errors:-Compile failed; see $log}"
  echo "✗ [$slug] LaTeX build failed:" >&2
  echo "${errors:-  (no error lines captured — see $log)}" >&2
  return 1
}

# --- arg handling ---------------------------------------------------------
QUIET=0
ARGS=()
for a in "$@"; do
  case "$a" in
    -q|--quiet) QUIET=1 ;;
    *) ARGS+=("$a") ;;
  esac
done

if [ "${#ARGS[@]}" -eq 0 ]; then
  echo "usage: ./papers/build.sh <slug>|--all [-q]" >&2
  exit 2
fi

if [ "${ARGS[0]}" = "--all" ]; then
  rc=0
  for d in "$PAPERS_DIR"/*/; do
    slug="$(basename "$d")"
    [ "$slug" = "_lib" ] && continue
    [ -f "$d/paper.md" ] || continue
    build_one "$slug" "$QUIET" || rc=1
  done
  exit $rc
fi

build_one "${ARGS[0]}" "$QUIET"
