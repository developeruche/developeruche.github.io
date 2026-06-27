#!/usr/bin/env python3
"""Convert a <slug>.local.md body to .post-body HTML per the add-blog conventions.

Shared by BOTH the `add-blog` and `add-blog-page` skills (keep the two copies
identical). It pre-renders markdown to clean semantic HTML (no inline styles, no
classes) for the static site, and is deliberately robust to the real-world
markdown found in these posts:

  - LaTeX ($..$, $$..$$, \\(..\\), \\[..\\]) passed through verbatim for KaTeX,
    never wrapped in <code>/<pre>.
  - Fenced code + inline code escaped and protected from inline processing.
  - Headings, hr (---/***/___), and lists isolated even when not separated by
    blank lines from surrounding text.
  - Nested lists via indentation, tab-indented lists (leading tabs expanded),
    `-`/`*`/`+`/`•`/`‣`/`·` bullets, and a paragraph lead-in before a list.
  - External links get target/rel; bare http(s) URLs are auto-linked.

Usage:
  python3 md_to_body.py <slug>.local.md   # prints the HTML body to stdout
Then replace the line containing "<!-- BODY:REPLACE_ME -->" in blog-<slug>.html.
"""
import html, re, sys

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

_LIST_RE = re.compile(r"^( *)([-*+•‣·]|\d+[.)])\s+(.*)$")

def _indent(line):
    return len(line) - len(line.lstrip(" "))

def _expand_leading_tabs(line):
    m = re.match(r"^[ \t]*", line)
    return m.group().expandtabs(4) + line[m.end():]

def render_list(lines, inline):
    """Render a (possibly nested) markdown list block to HTML."""
    marker_indents = [len(m.group(1)) for l in lines if (m := _LIST_RE.match(l))]
    base = min(marker_indents) if marker_indents else _indent(lines[0])
    first_marker = next((l for l in lines if _LIST_RE.match(l)), lines[0])
    ordered = bool(re.match(r"^ *\d+[.)]\s+", first_marker))
    items = []  # each: [marker_text, [child_lines]]
    cur = None
    for ln in lines:
        m = _LIST_RE.match(ln)
        if m and len(m.group(1)) == base:
            if cur:
                items.append(cur)
            cur = [m.group(3), []]
        else:
            if cur is None:  # stray text before first marker — start an item
                cur = ["", []]
            cur[1].append(ln)
    if cur:
        items.append(cur)

    tag = "ol" if ordered else "ul"
    out = [f"<{tag}>"]
    for text, children in items:
        content = inline(text.strip())
        if children:
            content += _render_children(children, inline)
        out.append(f"<li>{content}</li>")
    out.append(f"</{tag}>")
    return "".join(out)

def _render_children(children, inline):
    """Render the indented content under a list item: sub-lists and/or text."""
    html_out = []
    i = 0
    n = len(children)
    while i < n:
        ln = children[i]
        if not ln.strip():
            i += 1
            continue
        m = _LIST_RE.match(ln)
        if m:
            # gather this sub-list: this marker line + all deeper/continuation lines
            sub_indent = len(m.group(1))
            sub = [ln]
            i += 1
            while i < n:
                nxt = children[i]
                if not nxt.strip():
                    sub.append(nxt); i += 1; continue
                if _indent(nxt) >= sub_indent:
                    sub.append(nxt); i += 1
                else:
                    break
            html_out.append(render_list(sub, inline))
        else:
            # continuation text line(s) — append as inline text to current item
            html_out.append(" " + inline(ln.strip()))
            i += 1
    return "".join(html_out)

def convert(md):
    placeholders = {}
    pid = [0]
    def stash(content):
        key = f"\x00PH{pid[0]}\x00"
        pid[0] += 1
        placeholders[key] = content
        return key

    lines = md.split("\n")

    # --- protect fenced code blocks first (line based) ---
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^\s*```(.*)$", line)
        if m:
            buf = []
            i += 1
            while i < len(lines) and not re.match(r"^\s*```\s*$", lines[i]):
                buf.append(lines[i]); i += 1
            i += 1  # skip closing fence
            code = esc("\n".join(buf))
            out_lines.append(stash(f"<pre><code>{code}</code></pre>"))
        else:
            out_lines.append(line)
            i += 1
    text = "\n".join(out_lines)

    # --- protect block math $$...$$ and \[...\] ---
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: stash(f"<p>$${m.group(1)}$$</p>"), text, flags=re.S)
    text = re.sub(r"\\\[(.+?)\\\]", lambda m: stash(f"<p>\\[{m.group(1)}\\]</p>"), text, flags=re.S)

    # --- normalize leading tabs to spaces so indentation is comparable ---
    text = "\n".join(_expand_leading_tabs(l) for l in text.split("\n"))

    # --- isolate heading lines that lack surrounding blank lines ---
    iso = []
    for ln in text.split("\n"):
        if re.match(r"^\s*#{1,6}\s+\S", ln) or re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", ln):
            if iso and iso[-1].strip() != "":
                iso.append("")
            iso.append(ln)
            iso.append("")
        else:
            iso.append(ln)
    text = "\n".join(iso)

    # --- block-level parsing ---
    blocks = re.split(r"\n\s*\n", text)
    htmlparts = []

    def inline(s):
        # protect inline math and inline code
        s = re.sub(r"\$(?!\$)((?:\\.|[^$\\])+?)\$", lambda m: stash("$" + m.group(1) + "$"), s)
        s = re.sub(r"\\\((.+?)\\\)", lambda m: stash("\\(" + m.group(1) + "\\)"), s)
        s = re.sub(r"`([^`]+?)`", lambda m: stash("<code>" + esc(m.group(1)) + "</code>"), s)
        # escape stray html
        s = esc(s)
        # images
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                   lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy" />', s)
        # links
        def link(m):
            t, u = m.group(1), m.group(2)
            if re.match(r"^https?://", u):
                return f'<a href="{u}" target="_blank" rel="noopener noreferrer">{t}</a>'
            return f'<a href="{u}">{t}</a>'
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, s)
        # autolink bare URLs (not already inside an href="" or >...</a>)
        s = re.sub(r'(?<![">=(/])(https?://[^\s<]+[^\s<.,;:)])',
                   r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
        s = re.sub(r"(?<![\w_])_(?!_)(.+?)(?<!_)_(?![\w_])", r"<em>\1</em>", s)
        return s

    for blk in blocks:
        raw = blk.strip("\n")
        if not raw.strip():
            continue
        stripped = raw.strip()

        # pure placeholder block (code/math)
        if re.fullmatch(r"\x00PH\d+\x00", stripped):
            htmlparts.append(stripped)
            continue

        # heading
        hm = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if hm and "\n" not in stripped:
            level = len(hm.group(1))
            level = max(2, level)  # demote # to h2
            htmlparts.append(f"<h{level}>{inline(hm.group(2).strip())}</h{level}>")
            continue

        # hr
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            htmlparts.append("<hr />")
            continue

        # blockquote
        if all(l.lstrip().startswith(">") for l in raw.split("\n")):
            inner = "\n".join(re.sub(r"^\s*>\s?", "", l) for l in raw.split("\n"))
            htmlparts.append(f"<blockquote>{inline(inner.strip())}</blockquote>")
            continue

        # table (github)
        bl = raw.split("\n")
        if len(bl) >= 2 and "|" in bl[0] and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", bl[1]) and "-" in bl[1]:
            def cells(row):
                row = row.strip()
                if row.startswith("|"): row = row[1:]
                if row.endswith("|"): row = row[:-1]
                return [c.strip() for c in row.split("|")]
            head = cells(bl[0])
            body = [cells(r) for r in bl[2:] if r.strip()]
            t = ["<table>", "<thead><tr>"] + [f"<th>{inline(c)}</th>" for c in head] + ["</tr></thead>", "<tbody>"]
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t += ["</tbody>", "</table>"]
            htmlparts.append("".join(t))
            continue

        # lists (supports nesting + an optional paragraph lead-in before the list)
        list_start = next((j for j, l in enumerate(bl) if _LIST_RE.match(l)), None)
        if list_start is not None:
            pre = [l.strip() for l in bl[:list_start] if l.strip()]
            if pre:
                htmlparts.append(f"<p>{inline(' '.join(pre))}</p>")
            htmlparts.append(render_list(bl[list_start:], inline))
            continue

        # paragraph (may contain inline placeholders / soft breaks)
        para = inline(raw.replace("\n", " ").strip())
        htmlparts.append(f"<p>{para}</p>")

    result = "\n        ".join(htmlparts)
    # restore placeholders (repeat to resolve nested)
    for _ in range(3):
        for k, v in placeholders.items():
            result = result.replace(k, v)
    return result

if __name__ == "__main__":
    md = open(sys.argv[1], encoding="utf-8").read()
    # strip leading H1 (title already in page header)
    md = re.sub(r"^\s*#\s+.+?(\n|$)", "", md, count=1)
    sys.stdout.write(convert(md))
