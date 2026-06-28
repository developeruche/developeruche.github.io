#!/usr/bin/env python3
"""
page_from_entry.py — generate the in-site blog page for a post whose entry
ALREADY EXISTS in data/blog.json.

Unlike add-blog (which creates the json entry from scratch), this assumes
data/blog.json is already populated with the post's title, tags, and thumbnail.
You only supply the markdown body and a highlight flag. It:

  1. Reads the post title from the markdown's first "# " heading (or --title).
  2. Finds the matching entry in data/blog.json (case-insensitive title match).
  3. Resolves the slug (from an existing `blog-<slug>.html` link, else the title)
     and the hero image (uses the entry's thumbnail; downloads it if remote).
  4. Downloads inline body images into assets/blogs/<slug>/ and rewrites the
     markdown to local paths (writes <slug>.local.md).
  5. Updates the entry: sets `highlight`, repoints `link` to `blog-<slug>.html`,
     and localizes `thumbnail` if it was remote. Title/tags are left untouched.
  6. Writes the SEO-complete page shell blog-<slug>.html (same template as
     add-blog) with a "<!-- BODY:REPLACE_ME -->" marker, and regenerates
     sitemap.xml / robots.txt.

It does NOT convert markdown→HTML — the calling agent does that, then replaces
the marker.

Shared logic (downloads, SEO head, sitemap) is imported from the sibling
add-blog skill so there is a single source of truth.

Usage:
  python3 page_from_entry.py --md /path/post.md --highlight true \
    [--title "Exact Title"] --root /abs/site/root
"""
import argparse
import html
import importlib.util
import json
import os
import re
from datetime import date

# ── Import shared helpers from the add-blog skill ─────────────────────────────
_HELPER = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "add-blog", "scripts", "new_blog.py"))
_spec = importlib.util.spec_from_file_location("new_blog", _HELPER)
nb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nb)  # type: ignore


def title_from_md(md: str):
    m = re.search(r"^\s*#\s+(.+?)\s*$", md, re.M)
    return m.group(1).strip() if m else None


def find_entry(data, title):
    key = title.strip().lower()
    for i, it in enumerate(data):
        if it.get("title", "").strip().lower() == key:
            return i
    return None


def slug_from_link(link):
    s = str(link or "").strip()
    m = re.match(r"^blog/([a-z0-9-]+)/(?:index\.html)?$", s)  # new: /blog/<slug>/
    if m:
        return m.group(1)
    m = re.match(r"^blog-(.+)\.html$", s)                      # legacy: blog-<slug>.html
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--highlight", default="false")
    ap.add_argument("--title", default=None,
                    help="Override the title used to match blog.json (else the md H1).")
    ap.add_argument("--slug", default=None,
                    help="Explicit SEO slug. Overrides the slug derived from the "
                         "entry's existing link/title (recommended for long titles).")
    ap.add_argument("--root", default=os.getcwd())
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    highlight = str(a.highlight).strip().lower() in ("true", "1", "yes")
    md = open(a.md, encoding="utf-8").read()

    title = a.title or title_from_md(md)
    if not title:
        raise SystemExit("ERROR: no title — add a '# Title' to the markdown or pass --title.")

    # 1. locate the existing entry
    bj_path = os.path.join(root, "data", "blog.json")
    data = json.load(open(bj_path, encoding="utf-8"))
    idx = find_entry(data, title)
    if idx is None:
        titles = "\n  - ".join(d.get("title", "") for d in data)
        raise SystemExit(
            f"ERROR: no blog.json entry titled {title!r}. This skill requires the "
            f"entry to exist already. Existing titles:\n  - {titles}")
    entry = data[idx]
    tags = entry.get("tags", []) or []

    # 2. slug + page name (explicit --slug wins, else existing link, else title)
    if a.slug:
        slug = nb.slugify(title, a.slug)
    else:
        slug = slug_from_link(entry.get("link")) or nb.slugify(title)
    page = f"blog/{slug}/index.html"
    link = f"blog/{slug}/"

    # 3. hero thumbnail (use entry's; download if remote)
    thumb = entry.get("thumbnail")
    if thumb and nb.is_remote(thumb):
        path = nb.download(thumb, os.path.join(root, "assets", "blogs", f"{slug}-cover"))
        thumb_rel = os.path.relpath(path, root).replace(os.sep, "/")
    elif thumb:
        thumb_rel = thumb  # already local
    else:
        raise SystemExit(
            f"ERROR: entry {title!r} has no thumbnail. Set one in blog.json first "
            "(or use the add-blog skill which downloads one from a URL).")

    # 4. body images → local
    md_local, mapping = nb.process_images(md, slug, root)
    local_md = os.path.join(os.path.dirname(os.path.abspath(a.md)), f"{slug}.local.md")
    with open(local_md, "w", encoding="utf-8") as f:
        f.write(md_local)

    # 5. update the entry in place (title/tags untouched)
    entry["highlight"] = highlight
    entry["link"] = link
    entry["thumbnail"] = thumb_rel
    data[idx] = entry
    with open(bj_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 6. SEO-complete page shell (same template as add-blog)
    tpl = open(os.path.join(os.path.dirname(_HELPER), "..", "templates",
                            "post.html.template"), encoding="utf-8").read()
    iso_date = date.today().isoformat()
    canonical = f"{nb.SITE_URL}/blog/{slug}/"
    og_image = f"{nb.SITE_URL}/{thumb_rel}"
    hero_src = "/" + thumb_rel if not thumb_rel.startswith("/") else thumb_rel
    desc = nb.make_description(md)
    words = len(re.findall(r"\w+", re.sub(r"```.*?```", "", md, flags=re.S)))
    read_time = max(1, round(words / 200))

    tags_html = "\n".join(f"          <span>{html.escape(t)}</span>" for t in tags) or "          "
    article_tags = "\n".join(
        f'  <meta property="article:tag" content="{html.escape(t, quote=True)}" />' for t in tags)
    jsonld = nb.build_jsonld(title, desc, tags, link, og_image, iso_date)
    hero_alt = f"{title} — thumbnail"

    out = (tpl
           .replace("{{TITLE}}", html.escape(title, quote=True))
           .replace("{{DESCRIPTION}}", html.escape(desc, quote=True))
           .replace("{{CANONICAL}}", canonical)
           .replace("{{OG_IMAGE}}", og_image)
           .replace("{{HERO_SRC}}", hero_src)
           .replace("{{HERO_ALT}}", html.escape(hero_alt, quote=True))
           .replace("{{ARTICLE_TAGS}}", article_tags)
           .replace("{{JSONLD}}", jsonld)
           .replace("{{DATE}}", iso_date)
           .replace("{{READ_TIME}}", str(read_time))
           .replace("{{TAGS_HTML}}", tags_html))
    page_path = os.path.join(root, "blog", slug, "index.html")
    os.makedirs(os.path.dirname(page_path), exist_ok=True)
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(out)

    # 7. sitemap + robots
    nb.regenerate_sitemap(root)

    print(json.dumps({
        "matched_title": title, "slug": slug, "page": page, "link": link,
        "thumbnail": thumb_rel, "og_image": og_image, "canonical": canonical,
        "tags": tags, "highlight": highlight, "read_time": read_time,
        "local_md": local_md, "images_downloaded": mapping,
        "body_marker": "<!-- BODY:REPLACE_ME -->", "sitemap": "regenerated",
    }, indent=2))


if __name__ == "__main__":
    main()
