#!/usr/bin/env python3
"""
Import a paper's markdown into the papers/ build tree.

Creates:
  papers/<slug>/paper.md    normalised body (title + abstract lifted out)
  papers/<slug>/meta.json   metadata pandoc and the page renderer both read
and upserts the matching entry in data/publications.json.

Normalisation matters because the LaTeX template numbers sections itself and
puts the title/abstract in the title block. Left as-is, a pasted paper would
render its title twice and show "1. 1. Introduction".
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def split_fences(md):
    """Yield (line, in_code) so transforms never touch fenced code blocks."""
    in_code = False
    for line in md.split("\n"):
        if line.lstrip().startswith("```"):
            yield line, in_code   # the fence itself is a boundary, not content
            in_code = not in_code
        else:
            yield line, in_code


def extract_title(lines):
    """First level-1 heading is the paper title; remove it from the body."""
    out, title = [], None
    for line, in_code in lines:
        if not in_code and title is None:
            m = re.match(r"^#\s+(.+?)\s*$", line)
            if m:
                title = m.group(1).strip()
                continue
        out.append((line, in_code))
    return title, out


def extract_abstract(lines):
    """Lift a leading '## Abstract' section out of the body."""
    body, abstract, grabbing, level = [], [], False, 0
    for line, in_code in lines:
        if not in_code:
            m = re.match(r"^(#+)\s*abstract\s*$", line, re.I)
            if m:
                grabbing, level = True, len(m.group(1))
                continue
            if grabbing and re.match(r"^#+\s", line):
                if len(re.match(r"^(#+)", line).group(1)) <= level:
                    grabbing = False
        if grabbing:
            abstract.append(line)
            continue
        body.append((line, in_code))
    text = " ".join(l.strip() for l in abstract if l.strip())
    return re.sub(r"\s+", " ", text).strip(), body


def strip_heading_numbers(lines):
    """'## 2.1 The RISC-V ISA' -> '## The RISC-V ISA' (LaTeX numbers these)."""
    out = []
    for line, in_code in lines:
        if not in_code:
            line = re.sub(r"^(#+)\s+\d+(?:\.\d+)*\.?\s+(?=\S)", r"\1 ", line)
        out.append((line, in_code))
    return out


def promote_headings(lines):
    """Shift headings up so top-level sections are '#', which pandoc maps to
    \\section. Without this, '##' becomes \\subsection and numbering reads 0.1."""
    levels = [len(re.match(r"^(#+)\s", l).group(1))
              for l, c in lines if not c and re.match(r"^#+\s", l)]
    if not levels:
        return lines
    shift = min(levels) - 1
    if shift <= 0:
        return lines
    return [(re.sub(r"^#{%d}" % shift, "", l) if (not c and re.match(r"^#+\s", l)) else l, c)
            for l, c in lines]


def title_case(tag):
    return " ".join(w if w.isupper() else w.capitalize() for w in tag.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True, help="path to the paper markdown")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--authors", required=True, help="comma-separated")
    ap.add_argument("--date", required=True)
    ap.add_argument("--title", default=None, help="overrides the markdown's H1")
    ap.add_argument("--subtitle", default=None)
    ap.add_argument("--shorttitle", default=None, help="running head")
    ap.add_argument("--abstract", default=None, help="overrides the Abstract section")
    ap.add_argument("--tags", default="", help="comma-separated")
    ap.add_argument("--venue", default="")
    ap.add_argument("--author-note", dest="author_note", default="")
    ap.add_argument("--link", action="append", default=[], help='repeatable "LABEL|URL"')
    ap.add_argument("--highlight", default="true")
    ap.add_argument("--no-toc", action="store_true")
    a = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.slug):
        sys.exit(f"error: slug must be lowercase-kebab-case, got {a.slug!r}")

    src = Path(a.md)
    if not src.is_file():
        sys.exit(f"error: markdown not found: {src}")

    lines = list(split_fences(src.read_text()))
    md_title, lines = extract_title(lines)
    md_abstract, lines = extract_abstract(lines)
    lines = promote_headings(strip_heading_numbers(lines))

    title = a.title or md_title
    abstract = a.abstract or md_abstract
    if not title:
        sys.exit("error: no title — pass --title or start the markdown with '# Title'")
    if not abstract:
        sys.exit("error: no abstract — pass --abstract or include an '## Abstract' section")

    body = "\n".join(l for l, _ in lines).strip() + "\n"
    body = re.sub(r"\n{3,}", "\n\n", body)

    authors = [x.strip() for x in a.authors.split(",") if x.strip()]
    tags = [x.strip() for x in a.tags.split(",") if x.strip()]
    links = []
    for spec in a.link:
        label, _, url = spec.partition("|")
        if not url:
            sys.exit(f"error: --link must be 'LABEL|URL', got {spec!r}")
        links.append({"label": label.strip(), "url": url.strip()})

    pdir = ROOT / "papers" / a.slug
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "paper.md").write_text(body)

    meta = {
        "title": title,
        "shorttitle": a.shorttitle or title,
        "author": authors,
        "date": a.date,
        "toc": not a.no_toc,
        "abstract": abstract,
        "slug": a.slug,
        "tags": tags,
        "links": links,
    }
    if a.subtitle:
        meta["subtitle"] = a.subtitle
    if a.author_note:
        meta["author-note"] = a.author_note
    (pdir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")

    # --- upsert data/publications.json ------------------------------------
    pj = ROOT / "data" / "publications.json"
    pubs = json.loads(pj.read_text())
    entry = {
        "title": title,
        "slug": a.slug,
        "authors": authors,
        "date": a.date,
        "venue": a.venue,
        "paper": f"assets/papers/{a.slug}.pdf",
        "tags": [title_case(t) for t in tags],
        "abstract": abstract,
        "links": [{"label": "READ PAPER", "url": f"/publications/{a.slug}/"}] + links,
        "highlight": a.highlight.lower() == "true",
        "thumbnail": None,
    }
    for i, p in enumerate(pubs):
        if p.get("slug") == a.slug:
            pubs[i] = entry
            break
    else:
        pubs.insert(0, entry)
    pj.write_text(json.dumps(pubs, indent=2, ensure_ascii=False) + "\n")

    print(f"✓ papers/{a.slug}/paper.md      ({len(body.splitlines())} lines)")
    print(f"✓ papers/{a.slug}/meta.json")
    print(f"✓ data/publications.json        (entry for {a.slug})")
    print(f"\nTitle:    {title}")
    print(f"Authors:  {', '.join(authors)}")
    print(f"Abstract: {abstract[:110]}…")


if __name__ == "__main__":
    main()
