---
name: add-blog
description: Add a new in-site blog post to developeruche.github.io from a title, thumbnail URL, highlight flag, and the post body in markdown. Populates data/blog.json, downloads the thumbnail and any inline images into assets/blogs/, and generates a styled blog-<slug>.html detail page that matches the blog-post.html design. Use when the user wants to publish/add a blog post, create a blog page, or wire markdown content into the site.
---

# Add Blog Post

Publishes a new blog post to the static site **developeruche.github.io**. Given a
title, a thumbnail URL, a highlight flag, and the post body in markdown, this
skill produces:

1. A new entry in `data/blog.json` (so it shows up on `blog.html` and, if
   highlighted, on the home page).
2. Downloaded image assets in `assets/blogs/` (thumbnail + every inline image).
3. A standalone styled detail page `blog-<slug>.html` that follows the
   `blog-post.html` design (shared nav/footer, blueprint/terminal aesthetic,
   `.post-*` styles).

The site has **no build step** — pages are plain static HTML. So this skill
*pre-renders* the markdown to HTML at authoring time rather than rendering it in
the browser.

## Inputs to collect
- **Title** — the post title (string).
- **Thumbnail** — a URL to the cover image, **or** a path to an already-local
  image (e.g. `assets/blogs/foo.png`); local paths are used as-is, not downloaded.
- **Highlight** — `true` or `false` (whether it appears in home-page highlights).
- **Markdown** — the full post body. If the user pasted it inline, save it to a
  temp file first (e.g. `/tmp/<something>.md`).

If any are missing, ask for them before proceeding.

## Workflow

Run everything from the **site root**
(`/Users/gregg/Documents/projects/PROJECTS/developeruche.github.io`).

### 1. Choose tags
Read the markdown and pick **2–4 tags**. Reuse the site's existing tag
vocabulary where it fits — inspect current tags first:

```bash
python3 -c "import json;print(sorted({t.lower() for b in json.load(open('data/blog.json')) for t in b['tags']}))"
```

Examples already in use: `zero knowledge`, `cryptography`, `snarks`, `evm`,
`blockchain`, `protocol`, `algo`, `zkvm`, `pq cryptography`. Match casing/style
of these (lowercase, spaces) for consistency — the UI normalizes display.

### 2. Run the scaffold script
This handles slug, downloads, image rewriting, the `blog.json` entry, and the
page shell. It does **not** convert the body.

```bash
python3 .claude/skills/add-blog/scripts/new_blog.py \
  --title "THE TITLE" \
  --thumbnail "https://.../cover.png" \
  --highlight true \
  --tags "zero knowledge, zkvm" \
  --md /tmp/post.md \
  --root "$(pwd)"
```

**Slug / URL:** by default a **short, SEO-friendly** slug is derived from the
title — stop-words dropped, capped to ~6 words / 50 chars so the URL isn't
truncated mid-word in search results. For long titles, pass an explicit
`--slug "zisk-zkvm-trace-generation"` to control the URL (front-load the real
keywords; the full title still lives in `<title>`/`<h1>`).

It prints a JSON summary. Note especially:
- `slug` and `page` (e.g. `blog-the-title.html`),
- `local_md` — the markdown with remote image URLs **rewritten to local paths**
  (`assets/blogs/<slug>/img-N.ext`). **Use this file**, not the original, when
  converting the body.
- `body_marker` — the literal string in the page you must replace.

### 3. Convert the body markdown → HTML
Use the shared converter script — it implements all the mapping/escaping/LaTeX
rules below and is hardened against real-world markdown (nested + tab-indented
lists, `•` bullets, headings/`---` without blank lines, paragraph-then-list
blocks, bare-URL autolinking):

```bash
python3 .claude/skills/add-blog/scripts/md_to_body.py <slug>.local.md > /tmp/body.html
```

Then open the generated `blog-<slug>.html` and **replace the line containing
`<!-- BODY:REPLACE_ME -->`** (inside `<div class="post-body">`) with that HTML.
(`md_to_body.py` is shared verbatim with the **add-blog-page** skill — keep the
two copies identical when you change either.) The mapping it follows:

Mapping rules (these classes are already styled in `assets/css/site.css` under
`.post-body`, so output **plain semantic HTML — no inline styles, no class
attributes**):

| Markdown | HTML |
| --- | --- |
| `# H1` | `<h1>` (avoid — the page already has the title as `<h1 class="post-title">`; demote `#` to `<h2>`) |
| `## H2` / `### H3` / `#### H4` | `<h2>` / `<h3>` / `<h4>` |
| paragraph | `<p>` |
| `**bold**` | `<strong>` |
| `*italic*` | `<em>` |
| `[text](url)` | `<a href="url" target="_blank" rel="noopener noreferrer">` for external; internal stays same-tab |
| `- item` / `1. item` | `<ul><li>` / `<ol><li>` |
| `> quote` | `<blockquote>` |
| `` `code` `` | `<code>` |
| ```` ```lang ... ``` ```` | `<pre><code>` |
| `![alt](assets/blogs/<slug>/img-N.ext)` | `<img src="assets/blogs/<slug>/img-N.ext" alt="alt" loading="lazy" />` |
| `---` | `<hr />` |
| table | `<table><thead><tr><th>…</tr></thead><tbody><tr><td>…</tr></tbody></table>` |

Notes:
- **Escape** literal `<`, `>`, `&` that appear in prose/code so they don't break
  the page.
- The hero image (thumbnail) is already placed in the header by the template —
  do not repeat it at the top of the body.
- Keep the existing `<a class="back-link">` links and `<header>` intact.

#### LaTeX / math (KaTeX)
The template loads **KaTeX auto-render**, so math works out of the box. Keep the
LaTeX **verbatim** when converting — do **not** markdown-format or alter what's
between delimiters:
- Inline: `$ ... $` or `\( ... \)`
- Block:  `$$ ... $$` or `\[ ... \]`

Rules:
- Pass the delimiters and their contents through **exactly** as written in the
  markdown — no reflowing, no smart-quotes, no converting `*`/`_` inside math.
- A backslash like `\\` (newline in a matrix/aligned block) must stay `\\` — in
  the HTML source that's literally two backslashes, so write `\\` (not `\`).
- Don't wrap math in `<code>`/`<pre>` unless you intend to show it as literal
  source — KaTeX **ignores** `code`/`pre`, so math there will NOT render.
- HTML-escaping `<`, `>`, `&` inside math is safe (KaTeX reads decoded
  textContent), but it's cleaner to leave plain `<`, `>` if the surrounding HTML
  still parses; always escape a literal `&` to `&amp;`.
- Block equations get `.katex-display` (already styled to scroll horizontally on
  mobile). No extra wrappers needed.

### 4. Verify
- Confirm the page exists and references resolve:
  ```bash
  ls assets/blogs/<slug>* ; python3 -c "import json;print(json.load(open('data/blog.json'))[0]['title'])"
  ```
- Serve and check the page renders with images, on-system styling, and that the
  card on `blog.html` links to `blog-<slug>.html`. Use the preview tools
  (`preview_start` with the `static` launch config, then open
  `/blog-<slug>.html` and `/blog.html`). Check the console for errors.

## SEO (handled automatically)
The page shell the script writes is SEO-complete — you don't add meta tags by
hand. Each generated post includes:
- Unique `<title>`, `<meta name="description">` (auto-extracted from the body,
  stripped of markdown/math, ≤155 chars), `author`, and
  `robots: index, follow, max-image-preview:large`.
- `<link rel="canonical">` and `og:url` pointing at `https://developeruche.com/…`
  (the canonical domain from `CNAME`).
- **Open Graph + Twitter** cards with **absolute** image URLs (relative URLs
  break social previews), `og:image:alt`, `article:published_time`, and one
  `article:tag` per tag.
- **JSON-LD `BlogPosting`** structured data (headline, description, image,
  datePublished/Modified, author `Person` with `sameAs` socials, publisher,
  `mainEntityOfPage`, keywords) — this is what drives Google rich results and
  AI/LLM answer engines in 2026.
- Semantic `<article>`, a real `<time datetime>` element, lazy-loaded images,
  and a single `<h1>` (the title) with `<h2>+` in the body.
- It also **regenerates `sitemap.xml`** (all top-level pages, dummy excluded)
  and creates `robots.txt` if missing.

What you still control for ranking quality: pick an accurate **title** and
**tags**, and make sure the **first paragraph** of the markdown reads as a good
search snippet (it becomes the description). If you want a custom description
later, edit the `<meta name="description">`, `og:description`,
`twitter:description`, and the JSON-LD `description` together.

## Conventions & gotchas
- **Pages live at repo root** (`blog-<slug>.html`) so the relative `assets/...`,
  `blog.html`, and `./assets/js/layout.js` paths resolve exactly like
  `blog-post.html`. Do not move them into a subfolder.
- The card link uses `blog.json`'s `link` field; the script sets it to
  `blog-<slug>.html`. Blog cards open links in a new tab (existing behavior).
- Re-running with the same title **replaces** that post's `blog.json` entry
  (idempotent) but leaves old image files in place — clean up manually if a slug
  changes.
- All thumbnails/images are downloaded locally; the site never hot-links remote
  images. If a download fails the script warns and continues — re-fetch or fix
  that image reference manually.
- `blog-post.html` remains the untouched dummy template/reference.
