#!/usr/bin/env python3
"""
Render publications/<slug>/index.html from data/publications.json.

Reads the entry (title, authors, date, abstract, tags, links) so the detail
page and the /publications row always state the same thing, fills the
publication template, and registers the URL in sitemap.xml.

Safe to re-run: it overwrites the page and leaves the sitemap entry alone if
it is already present. Run it again whenever the metadata changes.
"""
import argparse, datetime, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "publication.html.template"
SITE = "https://developeruche.com"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def pdf_filename(title):
    """Readable download name: 'Bridging Worlds: A…' -> 'Bridging-Worlds-A….pdf'"""
    base = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-")
    return (base[:80].rstrip("-") or "paper") + ".pdf"


def render(slug):
    pubs = json.loads((ROOT / "data" / "publications.json").read_text())
    entry = next((p for p in pubs if p.get("slug") == slug), None)
    if entry is None:
        sys.exit(f"error: no entry with slug {slug!r} in data/publications.json")
    if not entry.get("paper"):
        sys.exit(f"error: entry {slug!r} has no 'paper' field — nothing to render")

    pdf_rel = "/" + entry["paper"].lstrip("/")
    if not (ROOT / entry["paper"]).is_file():
        print(f"warning: {entry['paper']} does not exist yet — "
              f"run ./papers/build.sh {slug}", file=sys.stderr)

    title = entry["title"]
    authors = ", ".join(entry.get("authors") or ["Developer Uche"])
    abstract = entry.get("abstract", "")
    # Meta description: one trimmed sentence-ish blurb, not the whole abstract.
    desc = abstract if len(abstract) <= 300 else abstract[:297].rsplit(" ", 1)[0] + "…"
    canonical = f"{SITE}/publications/{slug}/"

    tags_html = "\n".join(
        f'          <span>{esc(t)}</span>' for t in entry.get("tags", []))

    venue = entry.get("venue")
    venue_block = (f'          <span class="sep" aria-hidden="true">·</span>\n'
                   f'          <span>{esc(venue)}</span>') if venue else ""

    # Every link except the one pointing at this very page.
    extra = []
    for l in entry.get("links", []):
        if l["url"].rstrip("/") == f"/publications/{slug}".rstrip("/"):
            continue
        internal = l["url"].startswith("/")
        tgt = "" if internal else ' target="_blank" rel="noopener noreferrer"'
        arrow = "→" if internal else "↗"
        extra.append(f'        <a class="btn-secondary" href="{esc(l["url"])}"{tgt}>'
                     f'{esc(l["label"])} <span aria-hidden="true">{arrow}</span></a>')

    jsonld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": title,
        "name": title,
        "abstract": abstract,
        "url": canonical,
        "datePublished": str(entry.get("date", "")),
        "inLanguage": "en",
        "keywords": ", ".join(entry.get("tags", [])),
        "author": [{"@type": "Person", "name": a} for a in (entry.get("authors") or ["Developer Uche"])],
        "publisher": {"@type": "Person", "name": "Developer Uche", "url": SITE + "/"},
        "isPartOf": {"@type": "WebSite", "name": "Developer Uche", "url": SITE + "/"},
        "encoding": {"@type": "MediaObject", "contentUrl": SITE + pdf_rel,
                     "encodingFormat": "application/pdf"},
    }

    out = TEMPLATE.read_text()
    for key, val in {
        "TITLE": esc(title),
        "TITLE_ATTR": esc(title),
        "DESCRIPTION": esc(desc),
        "AUTHORS": esc(authors),
        "DATE": esc(entry.get("date", "")),
        "VENUE_BLOCK": venue_block,
        "TAGS": tags_html,
        "ABSTRACT": esc(abstract),
        "PDF_URL": esc(pdf_rel),
        "PDF_FILENAME": esc(pdf_filename(title)),
        "EXTRA_LINKS": "\n".join(extra),
        "CANONICAL": esc(canonical),
        "JSONLD": json.dumps(jsonld, indent=2, ensure_ascii=False),
    }.items():
        out = out.replace("{{" + key + "}}", val)

    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        sys.exit(f"error: unfilled placeholders remain: {sorted(set(left))}")

    dest = ROOT / "publications" / slug / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    print(f"✓ publications/{slug}/index.html")

    update_sitemap(canonical)


def update_sitemap(loc):
    sm = ROOT / "sitemap.xml"
    s = sm.read_text()
    if loc in s:
        print("· sitemap.xml already lists this URL")
        return
    today = datetime.date.today().isoformat()
    block = (f"  <url>\n    <loc>{loc}</loc>\n"
             f"    <lastmod>{today}</lastmod>\n    <priority>0.7</priority>\n  </url>\n")
    s = s.replace("</urlset>", block + "</urlset>")
    sm.write_text(s)
    print("✓ sitemap.xml")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    render(ap.parse_args().slug)
