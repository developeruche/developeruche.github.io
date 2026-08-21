#!/usr/bin/env python3
"""
Annotate LaTeX errors with the source line they point at.

The author writes markdown, but pdflatex reports line numbers in the generated
paper.tex. Quoting the offending line makes the error findable in paper.md.

Usage:  annotate_errors.py <paper.tex>   # error lines on stdin
"""
import re, sys

tex = open(sys.argv[1], errors="replace").read().split("\n") if len(sys.argv) > 1 else []
out = []
for line in sys.stdin.read().split("\n"):
    out.append(line)
    m = re.match(r"^(?:\./)?\S*\.tex:(\d+):", line)
    if m:
        i = int(m.group(1)) - 1
        if 0 <= i < len(tex) and tex[i].strip():
            out.append("    → " + tex[i].strip()[:160])
print("\n".join(out).strip())
