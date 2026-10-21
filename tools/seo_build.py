#!/usr/bin/env python3
"""
seo_build.py — site-wide SEO pass for developeruche.github.io. Idempotent: run it
after adding or editing any blog post or note (the add-blog / add-note skills
call it automatically).

    python3 tools/seo_build.py

What it does
  1. Titles & descriptions  Applies data/seo.json overrides (keyword-led title
                            <= 60 chars, hand-written description <= 155 chars)
                            to <title>, meta description, OG, Twitter, JSON-LD.
  2. Related reading        Injects up to 3 related articles (by shared tags)
                            at the end of every blog post and note, between
                            <!-- RELATED:START/END --> markers.
  3. Crawlable listings     Fills the JS-rendered grids on /blog, /notes and
                            /notes/<cat>/ with a static list of links (the JS
                            replaces it on load), between <!-- SEO:FALLBACK -->.
  4. Structured data        Completes note TechArticle JSON-LD (image, dates,
                            publisher, mainEntityOfPage) and adds breadcrumbs.
  5. Images                 width/height + fetchpriority on hero images; builds
                            1200x630 JPEG social cards in assets/og/.
  6. Feed & housekeeping    feed.xml (RSS 2.0), <link rel="alternate">,
                            canonical internal links, sitemap lastmod.
"""
import datetime, email.utils, html, json, re
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # images are optional; everything else still runs
    Image = None

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://developeruche.com"
BRAND = "Developer Uche"
TODAY = datetime.date.today().isoformat()
NOTE_CATS = {
    "blockchain": ("Blockchain", "Blueprint diagram of a block header chain and Merkle tree"),
    "cryptography-zkp": ("Cryptography & ZKP", "Blueprint diagram of an arithmetic circuit and polynomial evaluation domain"),
    "artificial-intelligence": ("Artificial Intelligence", "Blueprint diagram of a transformer block"),
}
RSS_LINK = '<link rel="alternate" type="application/rss+xml" title="Developer Uche — Blog & Notes" href="/feed.xml" />'

esc = lambda s: html.escape(str(s), quote=True)


def read(p): return (ROOT / p).read_text(encoding="utf-8")
def write(p, s): (ROOT / p).write_text(s, encoding="utf-8")


def set_meta(h, attr, key, value):
    """Replace content of <meta {attr}="{key}" content="..."> if present."""
    pat = re.compile(r'(<meta %s="%s" content=")[^"]*(")' % (attr, re.escape(key)))
    return pat.sub(lambda m: m.group(1) + esc(value) + m.group(2), h, count=1)


def jsonld_blocks(h):
    return list(re.finditer(r'(<script type="application/ld\+json">)(.*?)(</script>)', h, re.S))


# ── 1. Collect every article ──────────────────────────────────────────────
def load_articles():
    seo = json.loads(read("data/seo.json"))
    arts = []
    for b in json.loads(read("data/blog.json")):
        link = "/" + b["link"].strip("/") + "/"
        if not link.startswith("/blog/"):
            continue
        arts.append(dict(kind="blog", path=link, file=link.strip("/") + "/index.html",
                         title=b["title"], tags=b.get("tags", []), cat="blog",
                         excerpt=b.get("excerpt") or ""))
    for n in json.loads(read("data/notes.json")):
        if not n.get("link"):          # external-only entries have no page here
            continue
        link = "/" + n["link"].strip("/") + "/"
        arts.append(dict(kind="note", path=link, file=link.strip("/") + "/index.html",
                         title=n["title"], tags=n.get("tags", []), cat=n["category"],
                         excerpt=n.get("excerpt") or ""))
    out = []
    for a in arts:
        if not (ROOT / a["file"]).is_file():
            continue
        h = read(a["file"])
        o = seo.get(a["path"], {})
        a["seo_title"] = o.get("title") or a["title"]
        m = re.search(r'<meta name="description" content="([^"]*)"', h)
        a["desc"] = o.get("description") or html.unescape(m.group(1) if m else a["excerpt"])
        d = re.search(r'"datePublished":\s*"([^"]+)"', h)
        a["date"] = d.group(1) if d else TODAY
        a["has_override"] = bool(o)
        out.append(a)
    return out


# ── 5a. Social cards ──────────────────────────────────────────────────────
def og_card(src_rel):
    """1200x630 JPEG for og:image (webp isn't accepted everywhere, multi-MB PNGs
    load slowly). Returns the absolute URL, or None if it can't be built."""
    if Image is None:
        return None
    src = ROOT / src_rel.lstrip("/")
    if not src.is_file():
        return None
    dest = ROOT / "assets/og" / (src.stem + ".jpg")
    if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
        dest.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(src).convert("RGB")
        w, h = im.size
        tw, th = 1200, 630
        scale = max(tw / w, th / h)
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
        l, t = (im.width - tw) // 2, (im.height - th) // 2
        im.crop((l, t, l + tw, t + th)).save(dest, "JPEG", quality=84, optimize=True, progressive=True)
    return f"{SITE}/assets/og/{dest.name}"


def hero_attrs(h):
    """width/height (no layout shift) and LCP priority on the hero image."""
    def fix(m):
        tag = m.group(0)
        if Image and "width=" not in tag:
            src = re.search(r'src="([^"]+)"', tag)
            p = ROOT / src.group(1).lstrip("/") if src else None
            if p and p.is_file():
                w, hh = Image.open(p).size
                tag = tag.replace("<img ", f'<img width="{w}" height="{hh}" ', 1)
        tag = tag.replace(' loading="lazy"', "")
        if "fetchpriority=" not in tag:
            tag = tag.replace("<img ", '<img fetchpriority="high" decoding="async" ', 1)
        return tag
    return re.sub(r'<img class="post-hero-img"[^>]*>', fix, h, count=1)


# ── 2. Related reading ────────────────────────────────────────────────────
def related_for(a, arts, k=3):
    tags = {t.lower() for t in a["tags"]}
    scored = []
    for b in arts:
        if b["path"] == a["path"]:
            continue
        shared = len(tags & {t.lower() for t in b["tags"]})
        score = shared * 2 + (1 if b["cat"] == a["cat"] else 0)
        if score:
            scored.append((-score, b["seo_title"], b))
    return [b for _, _, b in sorted(scored, key=lambda x: (x[0], x[1]))[:k]]


def related_html(items):
    lis = "\n".join(
        f'          <li><a href="{b["path"]}">{esc(b["seo_title"])}</a>'
        f'<span>{esc(b["desc"])}</span></li>' for b in items)
    return ("<!-- RELATED:START -->\n"
            '      <aside class="related" aria-label="Related reading">\n'
            '        <span class="section-label">// RELATED READING</span>\n'
            f'        <ul class="related-list">\n{lis}\n        </ul>\n'
            "      </aside>\n      <!-- RELATED:END -->")


def put_related(h, block):
    if "<!-- RELATED:START -->" in h:
        return re.sub(r"<!-- RELATED:START -->.*?<!-- RELATED:END -->", lambda _: block, h, flags=re.S)
    # before the closing back-link (the one carrying the margin-top style)
    m = list(re.finditer(r'\n(\s*)<a class="back-link"[^>]*style=', h))
    if m:
        i = m[-1].start()
        return h[:i] + "\n      " + block + h[i:]
    return h.replace("</article>", "      " + block + "\n    </article>", 1)


# ── 4. Structured data for notes ──────────────────────────────────────────
def enrich_note_jsonld(h, a, image):
    cat_name = NOTE_CATS.get(a["cat"], (a["cat"], ""))[0]
    url = SITE + a["path"]
    for m in jsonld_blocks(h):
        try:
            d = json.loads(m.group(2))
        except json.JSONDecodeError:
            continue
        if isinstance(d, dict) and d.get("@type") == "TechArticle":
            d["description"] = a["desc"]
            d.setdefault("image", [image] if image else [])
            d.setdefault("dateModified", d.get("datePublished", TODAY))
            d["mainEntityOfPage"] = {"@type": "WebPage", "@id": url}
            d["author"] = {"@type": "Person", "name": BRAND, "url": SITE + "/",
                           "sameAs": ["https://github.com/developeruche", "https://x.com/developeruche",
                                      "https://www.linkedin.com/in/developeruche",
                                      "https://hackmd.io/@0xdeveloperuche"]}
            d["publisher"] = {"@type": "Person", "name": BRAND, "url": SITE + "/"}
            new = json.dumps(d, indent=2, ensure_ascii=False)
            h = h[:m.start(2)] + "\n" + new + "\n  " + h[m.end(2):]
            break
    if '"BreadcrumbList"' not in h:
        crumbs = json.dumps({
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Notes", "item": SITE + "/notes"},
                {"@type": "ListItem", "position": 3, "name": f"{cat_name} Notes",
                 "item": f"{SITE}/notes/{a['cat']}/"},
                {"@type": "ListItem", "position": 4, "name": a["title"], "item": url},
            ]}, indent=2, ensure_ascii=False)
        h = h.replace("</head>", f'  <script type="application/ld+json">\n{crumbs}\n  </script>\n</head>', 1)
    return h


# ── per-article pass ──────────────────────────────────────────────────────
def process_article(a, arts):
    h = read(a["file"])
    title = a["seo_title"]
    full = f"{title} — {BRAND}" if len(title) <= 46 else title
    if a["has_override"] or a["kind"] == "note":
        h = re.sub(r"<title>.*?</title>", f"<title>{esc(full)}</title>", h, count=1, flags=re.S)
        h = set_meta(h, "name", "description", a["desc"])
        h = set_meta(h, "property", "og:description", a["desc"])
        h = set_meta(h, "name", "twitter:description", a["desc"])
        h = set_meta(h, "property", "og:title", title)
        h = set_meta(h, "name", "twitter:title", title)
        # JSON-LD description (+ headline when the H1 is over Google's 110 chars)
        for m in jsonld_blocks(h):
            body = m.group(2)
            nb = re.sub(r'("description":\s*)"(?:[^"\\]|\\.)*"', lambda x: x.group(1) + json.dumps(a["desc"], ensure_ascii=False), body, count=1)
            if len(a["title"]) > 110:
                nb = re.sub(r'("headline":\s*)"(?:[^"\\]|\\.)*"', lambda x: x.group(1) + json.dumps(title, ensure_ascii=False), nb, count=1)
            if nb != body:
                h = h[:m.start(2)] + nb + h[m.end(2):]
                break

    # social card
    cur = re.search(r'<meta property="og:image" content="([^"]+)"', h)
    if cur:
        src = cur.group(1).replace(SITE, "")
        if a["kind"] == "note":
            src = f"/assets/notes/{a['cat']}.png"
        card = og_card(src) if not src.startswith("/assets/og/") else cur.group(1)
        if card:
            h = set_meta(h, "property", "og:image", card)
            h = set_meta(h, "name", "twitter:image", card)
            if "og:image:width" not in h:
                h = h.replace(f'<meta property="og:image" content="{card}" />',
                              f'<meta property="og:image" content="{card}" />\n'
                              '  <meta property="og:image:width" content="1200" />\n'
                              '  <meta property="og:image:height" content="630" />', 1)
    if a["kind"] == "note":
        h = set_meta(h, "property", "og:image:alt", NOTE_CATS.get(a["cat"], ("", BRAND))[1])
        img = re.search(r'<meta property="og:image" content="([^"]+)"', h)
        h = enrich_note_jsonld(h, a, img.group(1) if img else None)

    h = hero_attrs(h)
    h = put_related(h, related_html(related_for(a, arts)))
    if "application/rss+xml" not in h:
        h = h.replace("</head>", f"  {RSS_LINK}\n</head>", 1)
    h = re.sub(r'href="/blog\.html"', 'href="/blog"', h)
    write(a["file"], h)


# ── 3. Crawlable listing fallbacks ────────────────────────────────────────
def fallback_list(items):
    lis = "\n".join(f'          <li><a href="{b["path"]}">{esc(b["seo_title"])}</a>'
                    f'<span>{esc(b["desc"])}</span></li>' for b in items)
    return ('<!-- SEO:FALLBACK -->\n        <ul class="seo-fallback">\n'
            f"{lis}\n        </ul>\n        <!-- /SEO:FALLBACK -->")


def fill_grid(page, grid_id, items):
    p = ROOT / page
    if not p.is_file():
        return
    h = p.read_text(encoding="utf-8")
    pat = re.compile(r'(<div[^>]*id="%s"[^>]*>)(.*?)(</div>)' % grid_id, re.S)
    m = pat.search(h)
    if not m or (m.group(2).strip() and "SEO:FALLBACK" not in m.group(2)):
        return
    h = h[:m.end(1)] + "\n        " + fallback_list(items) + "\n      " + h[m.start(3):]
    if "application/rss+xml" not in h:
        h = h.replace("</head>", f"  {RSS_LINK}\n</head>", 1)
    p.write_text(h, encoding="utf-8")


# ── 6. Feed, sitemap, housekeeping ────────────────────────────────────────
def build_feed(arts):
    items = []
    for a in sorted(arts, key=lambda x: x["date"], reverse=True):
        d = datetime.datetime.fromisoformat(a["date"]).replace(tzinfo=datetime.timezone.utc)
        cats = "".join(f"<category>{esc(t)}</category>" for t in a["tags"])
        items.append(
            f"    <item>\n      <title>{esc(a['seo_title'])}</title>\n"
            f"      <link>{SITE}{a['path']}</link>\n      <guid isPermaLink=\"true\">{SITE}{a['path']}</guid>\n"
            f"      <pubDate>{email.utils.format_datetime(d)}</pubDate>\n"
            f"      <description>{esc(a['desc'])}</description>\n      {cats}\n    </item>")
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n  <channel>\n'
            f"    <title>Developer Uche — Blog &amp; Notes</title>\n    <link>{SITE}/</link>\n"
            "    <description>Writing on zero-knowledge proofs, cryptography, the EVM, Bitcoin and Ethereum protocol research.</description>\n"
            "    <language>en</language>\n"
            f'    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml" />\n'
            + "\n".join(items) + "\n  </channel>\n</rss>\n")
    write("feed.xml", feed)


def touch_sitemap(paths):
    s = read("sitemap.xml")
    for p in paths:
        loc = re.escape(SITE + p)
        s = re.sub(r"(<loc>%s</loc>\s*<lastmod>)[^<]*" % loc, lambda m: m.group(1) + TODAY, s)
    write("sitemap.xml", s)


def main():
    arts = load_articles()
    for a in arts:
        process_article(a, arts)

    blogs = [a for a in arts if a["kind"] == "blog"]
    notes = [a for a in arts if a["kind"] == "note"]
    fill_grid("blog.html", "blog-grid", blogs)
    fill_grid("notes.html", "notes-grid", notes)
    for cat in NOTE_CATS:
        fill_grid(f"notes/{cat}/index.html", "notes-grid", [n for n in notes if n["cat"] == cat])

    build_feed(arts)
    touch_sitemap([a["path"] for a in arts] + ["/blog", "/notes"] + [f"/notes/{c}/" for c in NOTE_CATS])

    # the dummy post template must never be indexed
    bp = ROOT / "blog-post.html"
    if bp.is_file():
        h = bp.read_text(encoding="utf-8")
        if 'name="robots"' not in h:
            bp.write_text(h.replace("<head>", '<head>\n  <meta name="robots" content="noindex, nofollow" />', 1), encoding="utf-8")

    print(f"✓ SEO pass: {len(blogs)} posts, {len(notes)} notes, listings, feed.xml, sitemap lastmod")


if __name__ == "__main__":
    main()
