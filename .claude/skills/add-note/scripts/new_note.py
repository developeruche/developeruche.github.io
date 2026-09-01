#!/usr/bin/env python3
"""
Publish a study note: markdown -> detail page + notes.json entry + sitemap URL.

    python3 new_note.py --md data/notes-md/<slug>.md \
        --slug <slug> --category artificial-intelligence \
        --title "..." --excerpt "..." --tags "A, B, C" [--date YYYY-MM-DD]
        [--no-highlight] [--shift-headings]

Body conversion reuses the site's existing converter (add-blog's md_to_body.py)
so notes and blog posts render identically: LaTeX passes through for KaTeX,
GitHub tables, fenced code and nested lists all work.

--shift-headings demotes every heading one level. Needed only when the markdown
uses BOTH '#' and '##' as structural levels: the converter clamps with
max(2, level), so those two collapse into <h2> and the hierarchy reads flat.
Markdown whose top level is already '##' must NOT be shifted. Fenced code is
never touched either way.
"""
import argparse, datetime, html, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SKILL = Path(__file__).resolve().parents[1]
CONVERTER = ROOT / ".claude/skills/add-blog/scripts/md_to_body.py"
SITE = "https://developeruche.com"
CATEGORIES = {
    "blockchain": "Blockchain",
    "cryptography-zkp": "Cryptography & ZKP",
    "artificial-intelligence": "Artificial Intelligence",
}


def shift_headings(md):
    out, in_code = [], False
    for ln in md.split("\n"):
        if ln.lstrip().startswith("```"):
            in_code = not in_code
            out.append(ln); continue
        if not in_code and re.match(r"^#{1,5} ", ln):
            ln = "#" + ln
        out.append(ln)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--category", required=True, choices=sorted(CATEGORIES))
    ap.add_argument("--title", required=True)
    ap.add_argument("--excerpt", required=True)
    ap.add_argument("--tags", default="")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--no-highlight", action="store_true")
    ap.add_argument("--shift-headings", action="store_true")
    a = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.slug):
        sys.exit(f"error: slug must be lowercase-kebab-case, got {a.slug!r}")
    src = Path(a.md)
    if not src.is_file():
        sys.exit(f"error: markdown not found: {src}")

    if a.shift_headings:
        src.write_text(shift_headings(src.read_text()))
        print(f"· shifted headings down one level in {src}")

    body = subprocess.run([sys.executable, str(CONVERTER), str(src)],
                          capture_output=True, text=True, check=True).stdout

    cat_display = CATEGORIES[a.category]
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    url = f"{SITE}/notes/{a.category}/{a.slug}/"
    e = lambda s: html.escape(str(s), quote=True)

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "TechArticle",
        "headline": a.title, "description": a.excerpt, "url": url,
        "datePublished": a.date, "inLanguage": "en", "keywords": ", ".join(tags),
        "author": {"@type": "Person", "name": "Developer Uche", "url": SITE + "/"},
        "isPartOf": {"@type": "CollectionPage", "name": f"{cat_display} Notes",
                     "url": f"{SITE}/notes/{a.category}/"},
    }, indent=2)

    page = (SKILL / "templates/note.html.template").read_text()
    for k, v in {
        "BODY": body.rstrip("\n"),
        "JSONLD": jsonld,
        "TAGS": "\n".join(f"          <span>{e(t)}</span>" for t in tags),
        "TITLE": e(a.title),
        "DESCRIPTION": e(a.excerpt),
        "URL": url,
        "CAT": a.category,
        "CAT_DISPLAY": e(cat_display),
        "CAT_UPPER": e(cat_display.upper()),
        "DATE": a.date,
    }.items():
        page = page.replace("{{" + k + "}}", v)

    leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", page)))
    if leftover:
        sys.exit(f"error: unfilled placeholders: {leftover}")

    dest = ROOT / "notes" / a.category / a.slug / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page)
    print(f"✓ notes/{a.category}/{a.slug}/index.html  ({len(page):,} bytes)")

    # --- notes.json (upsert, newest first) --------------------------------
    nj = ROOT / "data/notes.json"
    notes = json.loads(nj.read_text())
    notes = [n for n in notes if n.get("slug") != a.slug]
    notes.insert(0, {
        "title": a.title, "slug": a.slug, "category": a.category, "date": a.date,
        "excerpt": a.excerpt, "tags": tags,
        "link": f"/notes/{a.category}/{a.slug}/",
        "highlight": not a.no_highlight, "thumbnail": None,
    })
    nj.write_text(json.dumps(notes, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ data/notes.json  ({len(notes)} notes)")

    # --- sitemap ----------------------------------------------------------
    sm = ROOT / "sitemap.xml"
    s = sm.read_text()
    loc = url
    if loc in s:
        print("· sitemap.xml already lists this URL")
    else:
        s = s.replace("</urlset>",
            f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{a.date}</lastmod>\n"
            f"    <priority>0.6</priority>\n  </url>\n</urlset>")
        sm.write_text(s)
        print("✓ sitemap.xml")


if __name__ == "__main__":
    main()
