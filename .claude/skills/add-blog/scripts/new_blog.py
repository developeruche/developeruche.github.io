#!/usr/bin/env python3
"""
new_blog.py — scaffold a new in-site blog post for developeruche.github.io.

Handles the deterministic, error-prone work so the model only has to convert the
post body to HTML afterwards:

  1. Slugify the title.
  2. Download the thumbnail into assets/blogs/<slug>-cover.<ext>.
  3. Find every image referenced in the markdown, download remote ones into
     assets/blogs/<slug>/img-N.<ext>, and rewrite the markdown to point at the
     local copies (writes <slug>.local.md next to the source).
  4. Upsert the post in data/blog.json (matched by title) with title, tags,
     highlight, thumbnail, and link = "blog-<slug>.html".
  5. Write the page shell blog-<slug>.html from templates/post.html.template,
     leaving a "<!-- BODY:REPLACE_ME -->" marker for the converted body.

It deliberately does NOT convert markdown→HTML — the calling agent does that,
applying the .post-body class conventions, then replaces the marker.

Usage:
  python3 new_blog.py \
    --title "My Post Title" \
    --thumbnail "https://.../cover.png" \
    --highlight true \
    --tags "zero knowledge, evm" \
    --md /path/to/post.md \
    --root /abs/path/to/site/root

Prints a JSON summary (slug, paths, read_time, local_md) to stdout.
"""
import argparse
import glob
import html
import json
import os
import re
import ssl
import sys
import urllib.request
from datetime import date, datetime, timezone

UA = "Mozilla/5.0 (compatible; developeruche-add-blog/1.0)"
SITE_URL = "https://developeruche.com"  # canonical domain (see CNAME)

# Prefer certifi's CA bundle if available; otherwise fall back to an unverified
# context (these are public images on a static personal site).
try:
    import certifi  # type: ignore
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:  # noqa: BLE001
    _SSL_CTX = ssl._create_unverified_context()

EXT_BY_TYPE = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg",
    "image/gif": ".gif", "image/webp": ".webp", "image/svg+xml": ".svg",
    "image/avif": ".avif",
}


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-")[:80] or "post"


def download(url: str, dest_noext: str) -> str:
    """Download url to dest_noext + detected extension. Returns final path."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as r:
        data = r.read()
        ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    ext = EXT_BY_TYPE.get(ctype) or os.path.splitext(url.split("?")[0])[1] or ".png"
    if not ext.startswith("."):
        ext = "." + ext
    path = dest_noext + ext
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return path


# Markdown image:  ![alt](url "title")   and HTML <img src="url">
MD_IMG = re.compile(r"!\[[^\]]*\]\(\s*(<?)([^)\s]+)\1(?:\s+\"[^\"]*\")?\s*\)")
HTML_IMG = re.compile(r"<img[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']", re.I)


def is_remote(u: str) -> bool:
    return u.startswith("http://") or u.startswith("https://")


def process_images(md: str, slug: str, root: str):
    """Download remote images, return (rewritten_md, [(orig,local), ...])."""
    urls = []
    for m in MD_IMG.finditer(md):
        urls.append(m.group(2))
    for m in HTML_IMG.finditer(md):
        urls.append(m.group(1))
    seen, mapping = {}, []
    n = 0
    for u in urls:
        if not is_remote(u) or u in seen:
            continue
        n += 1
        dest = os.path.join(root, "assets", "blogs", slug, f"img-{n}")
        try:
            path = download(u, dest)
        except Exception as e:  # noqa: BLE001
            print(f"WARN: failed to download image {u}: {e}", file=sys.stderr)
            continue
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        seen[u] = rel
        mapping.append((u, rel))
    rewritten = md
    for orig, rel in mapping:
        rewritten = rewritten.replace(orig, rel)
    return rewritten, mapping


def upsert_blog_json(root: str, title, tags, highlight, thumbnail, link):
    path = os.path.join(root, "data", "blog.json")
    data = json.load(open(path, encoding="utf-8"))
    entry = {
        "title": title, "tags": tags, "link": link,
        "highlight": highlight, "thumbnail": thumbnail,
    }
    for i, it in enumerate(data):
        if it.get("title", "").strip().lower() == title.strip().lower():
            data[i] = entry
            break
    else:
        data.insert(0, entry)  # newest first
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def make_description(md: str) -> str:
    """First meaningful prose, stripped of markdown/math, ~155 chars."""
    text = re.sub(r"```.*?```", " ", md, flags=re.S)         # code fences
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)      # block math
    text = re.sub(r"\$[^$]*\$", " ", text)                    # inline math
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)         # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # links -> text
    text = re.sub(r"[#>*`_~|]", " ", text)                    # md punctuation
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 155:
        text = text[:152].rsplit(" ", 1)[0] + "…"
    return text


def build_jsonld(title, desc, tags, page, og_image, iso_date):
    obj = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": desc,
        "image": [og_image],
        "datePublished": iso_date,
        "dateModified": iso_date,
        "inLanguage": "en",
        "keywords": ", ".join(tags),
        "url": f"{SITE_URL}/{page}",
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{SITE_URL}/{page}"},
        "author": {
            "@type": "Person",
            "name": "Developer Uche",
            "url": SITE_URL,
            "sameAs": [
                "https://github.com/developeruche",
                "https://x.com/developeruche",
                "https://www.linkedin.com/in/developeruche",
            ],
        },
        "publisher": {
            "@type": "Person",
            "name": "Developer Uche",
            "url": SITE_URL,
        },
    }
    return json.dumps(obj, indent=2, ensure_ascii=False)


def regenerate_sitemap(root: str):
    """Rebuild sitemap.xml from all top-level *.html pages."""
    # blog-post.html is the dummy scaffold/reference — keep it out of the index.
    exclude = {"blog-post.html"}
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(root, "*.html"))
                   if os.path.basename(p) not in exclude)
    now = datetime.now(timezone.utc).date().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        loc = SITE_URL + "/" + ("" if p == "index.html" else p)
        prio = "1.0" if p == "index.html" else ("0.8" if p in ("blog.html", "projects.html", "publications.html") else "0.6")
        lines += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{now}</lastmod>",
                  f"    <priority>{prio}</priority>", "  </url>"]
    lines.append("</urlset>")
    with open(os.path.join(root, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    robots = os.path.join(root, "robots.txt")
    if not os.path.exists(robots):
        with open(robots, "w", encoding="utf-8") as f:
            f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--thumbnail", required=True)
    ap.add_argument("--highlight", default="false")
    ap.add_argument("--tags", default="")
    ap.add_argument("--md", required=True)
    ap.add_argument("--root", default=os.getcwd())
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    slug = slugify(a.title)
    highlight = str(a.highlight).strip().lower() in ("true", "1", "yes")
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]

    md = open(a.md, encoding="utf-8").read()

    # 1. thumbnail
    thumb = download(a.thumbnail, os.path.join(root, "assets", "blogs", f"{slug}-cover"))
    thumb_rel = os.path.relpath(thumb, root).replace(os.sep, "/")

    # 2. body images
    md_local, mapping = process_images(md, slug, root)
    local_md = os.path.join(os.path.dirname(os.path.abspath(a.md)), f"{slug}.local.md")
    with open(local_md, "w", encoding="utf-8") as f:
        f.write(md_local)

    # 3. read time
    words = len(re.findall(r"\w+", re.sub(r"```.*?```", "", md, flags=re.S)))
    read_time = max(1, round(words / 200))

    # 4. blog.json
    page = f"blog-{slug}.html"
    upsert_blog_json(root, a.title, tags, highlight, thumb_rel, page)

    # 5. page shell from template (with full SEO head)
    tpl_path = os.path.join(os.path.dirname(__file__), "..", "templates", "post.html.template")
    tpl = open(os.path.abspath(tpl_path), encoding="utf-8").read()

    iso_date = date.today().isoformat()
    canonical = f"{SITE_URL}/{page}"
    og_image = f"{SITE_URL}/{thumb_rel}"            # absolute URL (required by OG)
    desc = make_description(md)
    desc_attr = html.escape(desc, quote=True)
    title_attr = html.escape(a.title, quote=True)
    hero_alt = f"{a.title} — thumbnail"
    hero_alt_attr = html.escape(hero_alt, quote=True)

    tags_html = "\n".join(f"          <span>{html.escape(t)}</span>" for t in tags) or "          "
    article_tags = "\n".join(
        f'  <meta property="article:tag" content="{html.escape(t, quote=True)}" />' for t in tags
    )
    jsonld = build_jsonld(a.title, desc, tags, page, og_image, iso_date)

    out = (tpl
           .replace("{{TITLE}}", title_attr)
           .replace("{{DESCRIPTION}}", desc_attr)
           .replace("{{CANONICAL}}", canonical)
           .replace("{{OG_IMAGE}}", og_image)
           .replace("{{HERO_SRC}}", thumb_rel)
           .replace("{{HERO_ALT}}", hero_alt_attr)
           .replace("{{ARTICLE_TAGS}}", article_tags)
           .replace("{{JSONLD}}", jsonld)
           .replace("{{DATE}}", iso_date)
           .replace("{{READ_TIME}}", str(read_time))
           .replace("{{TAGS_HTML}}", tags_html))
    with open(os.path.join(root, page), "w", encoding="utf-8") as f:
        f.write(out)

    # 6. sitemap.xml + robots.txt (site-level SEO)
    regenerate_sitemap(root)

    print(json.dumps({
        "slug": slug, "page": page, "thumbnail": thumb_rel,
        "canonical": canonical, "og_image": og_image,
        "read_time": read_time, "tags": tags, "highlight": highlight,
        "local_md": local_md, "images_downloaded": mapping,
        "body_marker": "<!-- BODY:REPLACE_ME -->",
        "sitemap": "regenerated", "description": desc,
    }, indent=2))


if __name__ == "__main__":
    main()
