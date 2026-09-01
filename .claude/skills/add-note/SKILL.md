---
name: add-note
description: Publish a study note to developeruche.github.io from a markdown file, a slug, and one of the three note categories (blockchain, cryptography-zkp, artificial-intelligence). Renders the markdown to a styled detail page at /notes/<category>/<slug>/ with KaTeX math, adds the entry to data/notes.json so it appears on the category listing and the home page, and registers the URL in the sitemap. Use when the user wants to add a study note, publish notes, or wire markdown study material into the site.
---

# Add Note

Publishes a study note. Given the note's markdown, a slug, and a category, this produces:

1. `data/notes-md/<slug>.md` — the markdown source, kept like `data/blog-md/`.
2. `notes/<category>/<slug>/index.html` — the detail page, served at **`/notes/<category>/<slug>/`**.
3. An entry in `data/notes.json`, which drives the category listing, the note count on `/notes`, and (when `highlight` is true) the home page Notes section.
4. A `sitemap.xml` entry.

The site has **no build step**, so the page is pre-rendered at authoring time.

## Inputs

- **Markdown** — the note body. Save it to `data/notes-md/<slug>.md` first.
- **Slug** — lowercase-kebab-case; becomes the URL.
- **Category** — exactly one of `blockchain`, `cryptography-zkp`, `artificial-intelligence`.
- **Title**, **excerpt** (shown on the cards), **tags**, optional **date**.

## Workflow

Save the markdown, then run one command from the site root:

```bash
python3 .claude/skills/add-note/scripts/new_note.py \
  --md data/notes-md/my-note.md \
  --slug my-note \
  --category artificial-intelligence \
  --title "My Note" \
  --excerpt "One or two sentences for the listing card." \
  --tags "Machine Learning, Regression"
```

Add `--no-highlight` to keep it off the home page.

### Do not pass `--date` unless the user gave you one

It defaults to the real system date, which is almost always what you want.
**Never take a date from `git log`, a PR merge timestamp, or anything else on
screen** — those are the dates of *other* work and reading one off is how both
of the first two notes shipped misdated. If a specific date is needed, get it
from the user or from `date +%Y-%m-%d`, never by inference.

A note's date appears in **five** places: `data/notes.json`, and three sites in
the page (`article:published_time`, the `<time>` element, and the JSON-LD
`datePublished`), plus the `sitemap.xml` `lastmod`. Re-running this script
updates the first four; check the sitemap separately when correcting a date.

### Strip the H1 first

The page renders the title itself, so remove the markdown's own `# Title` line. Leaving it produces the title twice.

### `--shift-headings`

Body conversion reuses `add-blog/scripts/md_to_body.py`, which clamps heading levels with `max(2, level)`. That means **`#` and `##` both become `<h2>`**.

- Markdown whose top level is already `##` → **do not shift**. It maps correctly (`##`→h2, `###`→h3).
- Markdown using **both** `#` and `##` as structural levels (e.g. `# Part I` containing `## 1.1`) → pass `--shift-headings`, or the two collapse into one level and the hierarchy reads flat.

The flag rewrites the source file in place and never touches fenced code, so `#` comments in Python blocks are safe.

## Verify

```bash
python3 serve.py 8000
```

Open `/notes/<category>/<slug>/` and check:

- **Math** — every `$…$` and `$$…$$` typeset. Count `.katex` nodes and confirm no raw `$` survives outside `pre`/`code`/`.katex`.
- **Tables and code** — present, and math inside table cells rendered.
- **Headings** — the hierarchy matches the source's intent.
- Console clean. (KaTeX "slow network / fallback font" messages are info, not errors.)
- `/notes` count incremented, and the note appears on the category listing.

## Notes on content

- Excerpts are for the card, not the page; write one or two sentences that say what the note covers.
- Don't repeat the category in the title. The page already labels itself `// STUDY NOTE · <CATEGORY>`, so "Linear Regression" beats "Linear Regression — Lesson Note", which also yields a double-dash browser title.
