---
name: add-blog-page
description: Generate the in-site blog detail page for a post whose entry ALREADY exists in data/blog.json. Inputs are just the markdown body and a highlight flag (true/false) — title, tags, and thumbnail are read from the existing blog.json entry. Downloads inline images, builds an SEO-complete blog-<slug>.html that matches blog-post.html, and refreshes the sitemap. Use when blog.json is already populated and you only need to render the page from markdown.
---

# Add Blog Page (entry already in blog.json)

A streamlined variant of the **add-blog** skill. Use it when the post is
**already listed in `data/blog.json`** (title, tags, thumbnail set) and you just
need to turn a markdown body into the styled, SEO-complete detail page.

**Inputs:**
- **Markdown** — the full post body. Its first `# Heading` is used to match the
  blog.json entry (or pass `--title "..."` to match explicitly). If pasted
  inline, save it to a temp file first.
- **Highlight** — `true` or `false`.

Everything else (title, tags, thumbnail) comes from the existing entry. If the
entry doesn't exist yet, use the **add-blog** skill instead (it creates it).

> Depends on the sibling **add-blog** skill: it reuses that skill's helper
> script (`new_blog.py`) and page template. Keep both skills present.

## Workflow

Run from the **site root**
(`/Users/gregg/Documents/projects/PROJECTS/developeruche.github.io`).

### 1. Run the page generator
```bash
python3 .claude/skills/add-blog-page/scripts/page_from_entry.py \
  --md /tmp/post.md \
  --highlight true \
  --root "$(pwd)"
# add --title "Exact Title From blog.json" if the md has no clean H1
```
**Slug / URL:** by default the slug comes from the entry's existing
`blog-<slug>.html` link, else a short SEO slug from the title. For a long title,
pass `--slug "zisk-zkvm-trace-generation"` to set a short, keyword-front-loaded
URL (better for SEO — search results truncate long URLs mid-word).

It prints a JSON summary. Note:
- `matched_title` — confirm it matched the post you intended.
- `slug` / `page` (e.g. `blog-<slug>.html`).
- `local_md` — markdown with image URLs rewritten to local paths. **Convert this
  file**, not the original.
- `body_marker` — the string to replace in the page.

What it changed in `data/blog.json` for that entry: `highlight`, `link`
(→ `blog-<slug>.html`), and `thumbnail` (localized if it was a remote URL).
**Title and tags are left untouched.**

### 2. Convert the body markdown → HTML
Identical to add-blog. Read `local_md`, convert to clean semantic HTML using the
`.post-body` conventions (no inline styles, no classes), and replace the line
containing `<!-- BODY:REPLACE_ME -->` inside `<div class="post-body">`.

See the **add-blog** SKILL.md "Convert the body" section for the full mapping
table. Key reminders:
- Demote a leading `#` to `<h2>` (the page `<h1>` is the title already).
- External links: `target="_blank" rel="noopener noreferrer"`.
- Images: `<img src="assets/blogs/<slug>/img-N.ext" alt="…" loading="lazy" />`.
- **LaTeX** (`$…$`, `$$…$$`, `\(…\)`, `\[…\]`) — pass through **verbatim**;
  KaTeX is already wired in the template. Never put math in `code`/`pre`.
- Escape literal `<`, `>`, `&` in prose/code.

### 3. Verify
- `python3 -c "import json;e=[b for b in json.load(open('data/blog.json')) if b['title'].lower()=='<title>'.lower()][0];print(e['link'],e['highlight'])"`
- Serve with the `static` preview config and open `/blog-<slug>.html` and
  `/blog.html`; confirm images, math, on-system styling, and that the card links
  to the new page. Check the console for errors.

## SEO (automatic)
The page is SEO-complete out of the box — same as add-blog: unique title +
description (auto-extracted), canonical, Open Graph + Twitter cards with
**absolute** image URLs, `article:*` tags, JSON-LD `BlogPosting` structured
data, semantic `<time>`, lazy images, and a regenerated `sitemap.xml`
(+`robots.txt`). You only need to pick a good highlight value and ensure the
markdown's first paragraph reads as a solid search snippet.

## Gotchas
- **No matching entry → it errors** and lists existing titles. That's by design;
  this skill never invents a `blog.json` entry.
- Pages live at **repo root** (`blog-<slug>.html`) so relative asset paths
  resolve; don't relocate them.
- Re-running regenerates the page and re-updates the same entry (idempotent);
  old downloaded images are left in place if a slug changes — clean up manually.
- If the entry's `thumbnail` is still a remote URL, it's downloaded and the entry
  is updated to the local path. If it's `null`, the script errors — set a
  thumbnail in blog.json first.
