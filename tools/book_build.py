#!/usr/bin/env python3
"""
Build the multi-page notes book from data/notes-md/<book>/book.json.

    python3 tools/book_build.py computational-proof-systems

Writes the contents page at /notes/<category>/<book>/ and one page per finished
entry ("done": true) at /notes/<category>/<book>/<slug>/, with previous/next
links in reading order. Unfinished entries show on the contents page as plain
text. Body conversion reuses add-blog's md_to_body.py.

While "published" is false the pages are noindex and tools/seo_build.py skips
them, so a half-imported book never reaches the sitemap, feed or listings. Set
it to true once the book is complete, add the notes.json card, and re-run this
and seo_build. Published pages get a sitemap entry and related reading, but only
the contents page is listed: the book is one card, not one card per page.
"""
import html, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONVERTER = ROOT / ".claude/skills/add-blog/scripts/md_to_body.py"
TEMPLATE = ROOT / "tools/book-page.html.template"
SITE = "https://developeruche.com"
CATEGORIES = {"cryptography-zkp": "Cryptography & ZKP"}
e = lambda s: html.escape(str(s), quote=True)


def inline_links(s):
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  lambda m: f'<a href="{e(m.group(2))}" target="_blank" rel="noopener noreferrer">{e(m.group(1))}</a>',
                  e(s).replace("&#x27;", "'"))


def render(**f):
    page = TEMPLATE.read_text()
    for k, v in f.items():
        page = page.replace("{{" + k + "}}", v)
    leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", page)))
    if leftover:
        sys.exit(f"error: unfilled placeholders: {leftover}")
    return page


def jsonld(title, desc, url, date, tags, book, base):
    d = {"@context": "https://schema.org", "@type": "TechArticle",
         "headline": title, "description": desc, "url": url,
         "datePublished": date, "inLanguage": "en", "keywords": ", ".join(tags),
         "author": {"@type": "Person", "name": "Developer Uche", "url": SITE + "/"},
         "isPartOf": {"@type": "Book", "name": book["title"], "url": base}}
    return json.dumps(d, indent=2, ensure_ascii=False)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = ROOT / "data/notes-md" / sys.argv[1]
    book = json.loads((src / "book.json").read_text())
    cat, slug = book["category"], book["slug"]
    cat_display = CATEGORIES[cat]
    path = f"/notes/{cat}/{slug}/"
    base = SITE + path
    robots = "index, follow, max-image-preview:large" if book["published"] else "noindex, nofollow"
    common = dict(ROBOTS=robots, CAT=cat, CAT_DISPLAY=e(cat_display), DATE=book["date"])

    done = [(c, p) for c in book["chapters"] for p in c["pages"] if p.get("done")]
    for i, (chapter, p) in enumerate(done):
        md = src / f"{p['slug']}.md"
        body = subprocess.run([sys.executable, str(CONVERTER), str(md)],
                              capture_output=True, text=True, check=True).stdout.rstrip("\n")
        prev_p = done[i - 1][1] if i else None
        next_p = done[i + 1][1] if i + 1 < len(done) else None
        cell = lambda q, cls, label: (
            f'<a class="{cls}" href="{path}{q["slug"]}/"><span>{label}</span>{e(q["title"])}</a>' if q else "<span></span>")
        nav = ('      <nav class="book-nav" aria-label="Book pages">\n'
               f'        {cell(prev_p, "book-nav-prev", "← Previous")}\n'
               f'        {cell(next_p, "book-nav-next", "Next →")}\n'
               '      </nav>\n'
               f'      <a class="back-link" href="{path}" style="margin-top: var(--space-lg);">← {e(book["title"])} contents</a>')
        url = f"{base}{p['slug']}/"
        page = render(**common, TITLE=e(p["title"]), SEO_TITLE=e(p.get("seo_title", p["title"])),
                      DESCRIPTION=e(p["description"]), URL=url, BODY=body, NAV=nav,
                      BACK_HREF=path, BACK_LABEL=e(book["title"]) + " contents",
                      LABEL=e(f'{book["title"].upper()} · {chapter["title"].split(":")[0].upper()}'),
                      JSONLD=jsonld(p["title"], p["description"], url, book["date"], p.get("tags", []), book, base))
        out = ROOT / "notes" / cat / slug / p["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)

    # --- contents page ----------------------------------------------------
    parts = [f"<p>{inline_links(book['intro'])}</p>"]
    for c in book["chapters"]:
        items = "".join(
            f'<li><a href="{path}{p["slug"]}/">{e(p["title"])}</a></li>' if p.get("done")
            else f'<li class="book-toc-pending">{e(p["title"])}</li>' for p in c["pages"])
        parts.append(f'<h2>{e(c["title"])}</h2>\n<ul class="book-toc">{items}</ul>')
    page = render(**common, TITLE=e(book["title"]), SEO_TITLE=e(book["title"]),
                  DESCRIPTION=e(book["description"]), URL=base, BODY="\n".join(parts),
                  NAV=f'      <a class="back-link" href="/notes/{cat}/" style="margin-top: var(--space-lg);">← Back to {e(cat_display)} notes</a>',
                  BACK_HREF=f"/notes/{cat}/", BACK_LABEL=f"Back to {e(cat_display)} notes",
                  LABEL="STUDY NOTES · " + e(cat_display.upper()),
                  JSONLD=jsonld(book["title"], book["description"], base, book["date"], ["Zero-Knowledge", "Cryptography"], book, base))
    (ROOT / "notes" / cat / slug / "index.html").write_text(page)

    # --- titles and snippets for tools/seo_build.py -----------------------
    if book["published"]:
        seo_path = ROOT / "data/seo.json"
        seo = json.loads(seo_path.read_text())
        seo[path] = {"title": book["title"], "description": book["description"]}
        for _, p in done:
            seo[f"{path}{p['slug']}/"] = {"title": p.get("seo_title", p["title"]), "description": p["description"]}
        seo_path.write_text(json.dumps(seo, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ {path}  ({len(done)} pages built, published={book['published']})")


if __name__ == "__main__":
    main()
