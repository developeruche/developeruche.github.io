---
name: add-paper
description: Publish a research paper to developeruche.github.io from a markdown file, date, authors, and slug. Converts the markdown into a typeset academic PDF via pandoc + pdflatex, adds the entry to data/publications.json, and generates the publication detail page at /publications/<slug>/ with an in-page PDF reader. Use when the user wants to add/publish a paper, wire a research draft into the site, create a publication detail page, or set up live preview while writing a paper.
---

# Add Paper

Publishes a paper to the static site **developeruche.github.io**. Given the
paper's markdown plus a date, authors and slug, this produces:

1. `papers/<slug>/paper.md` — the normalised source the author keeps editing.
2. `papers/<slug>/meta.json` — title, authors, date, abstract, tags, links.
3. `assets/papers/<slug>.pdf` — the typeset paper (pandoc → LaTeX → pdflatex).
4. An entry in `data/publications.json`, so the paper appears on
   `/publications.html` and (if highlighted) the home page.
5. `publications/<slug>/index.html` — the detail page at **`/publications/<slug>/`**,
   showing the same title/authors/abstract/tags as the listing row plus an
   in-page PDF reader and a download button.
6. A `sitemap.xml` entry.

The site has **no build step**, so the PDF and the detail page are both
generated at authoring time and committed.

## Inputs to collect

- **Markdown** — the paper body. If pasted inline, save it to a temp file first.
- **Slug** — lowercase-kebab-case, e.g. `risc-v-evm-integration-performance-feasibility`.
  This becomes the URL `/publications/<slug>/`.
- **Authors** — comma-separated.
- **Date** — free text as it should print (`2025`, `April 2025`, `2025-04-20`).

Optional: `--title` and `--abstract` (otherwise taken from the markdown's `# H1`
and its `## Abstract` section), `--subtitle`, `--shorttitle` (running head),
`--tags`, `--venue`, `--author-note`, repeatable `--link "LABEL|URL"`,
`--highlight true|false`, `--no-toc`.

Ask for anything missing before proceeding. **Never invent a date** — if the
user has not given one, ask.

## Workflow

Run everything from the site root
(`/Users/gregg/Documents/projects/PROJECTS/developeruche.github.io`).

### 1. Import the markdown

```bash
python3 .claude/skills/add-paper/scripts/import_paper.py \
  --md /tmp/paper.md \
  --slug my-paper-slug \
  --authors "Developeruche" \
  --date "2025" \
  --tags "RISC-V, EVM, Blockchain" \
  --venue "Independent research — full draft report" \
  --author-note "x.com/developeruche · github.com/developeruche" \
  --link "RUST PoC CODE|https://github.com/developeruche/…" \
  --highlight true
```

This normalises the markdown, which matters because the LaTeX template numbers
sections itself and prints the title/abstract in the title block:

- the first `# Heading` is lifted out as the title,
- a `## Abstract` section is lifted out into `meta.json`,
- manual section numbers are stripped (`## 2.1 Foo` → `## Foo`),
- headings are promoted so top-level sections are `#` — otherwise pandoc maps
  `##` to `\subsection` and the numbering renders as `0.1`.

Fenced code blocks are never touched by any of these transforms.

### 2. Choose tags

Reuse the site's existing vocabulary where it fits:

```bash
python3 -c "import json;print(sorted({t for p in json.load(open('data/publications.json')) for t in p['tags']}))"
```

### 3. Build the PDF

```bash
./papers/build.sh <slug>
```

Prints the page count on success. On failure it prints the LaTeX errors and
**leaves the previously published PDF untouched**, so the live page never
serves a broken file.

### 4. Generate the detail page

```bash
python3 .claude/skills/add-paper/scripts/render_publication.py <slug>
```

Reads the entry back out of `data/publications.json`, so the row and the detail
page can never disagree. Re-run it any time the metadata changes.

### 5. Verify

Serve the site and check both pages actually render:

```bash
./papers/dev.sh <slug>
```

- `/publications.html` — the row appears, READ PAPER points at `/publications/<slug>/`
- `/publications/<slug>/` — title, authors, abstract, tags, and the PDF reader
- `/papers/preview.html?slug=<slug>` — live preview while editing

Check the browser console: the reader should report the page count in the
viewer bar. If pdf.js fails to load it silently falls back to the browser's own
PDF plugin, which is a valid state but worth noticing.

## Live editing

The point of the setup is that a paper is never restarted from scratch:

```bash
./papers/dev.sh <slug>
```

starts a static server **and** a watcher. Every save of `paper.md` or
`meta.json` recompiles the PDF and the preview refreshes itself. A LaTeX error
shows over the last good render instead of blanking the page.

After editing, rebuild and re-render before committing:

```bash
./papers/build.sh <slug> && python3 .claude/skills/add-paper/scripts/render_publication.py <slug>
```

## What to commit

`papers/<slug>/`, `assets/papers/<slug>.pdf`, `publications/<slug>/index.html`,
`data/publications.json`, `sitemap.xml`. Build intermediates in
`papers/*/.build/` and `.build-status.json` are gitignored.

## Writing rules for the paper itself

The template is a single-column technical report: Times-family text (newtx),
Inconsolata for code, navy accents, numbered sections, a table of contents, and
an abstract block. When drafting or editing prose, follow normal technical
paper conventions:

- Abstract states problem, method, findings, and contribution — no citations.
- Numbered sections; keep the conventional arc (Introduction → Background →
  Methodology → Results → Discussion → Conclusion → References).
- Claims that rest on measurements need the measurement, or explicit hedging.
  Do not upgrade a draft's tentative language into confident language.
- Keep the author's voice and terminology. Fix outright spelling errors, but
  **never silently rewrite technical claims** — surface them instead.
- Code blocks should be tagged with a language for highlighting (` ```rust `,
  ` ```asm `). Long lines wrap automatically; they are not truncated.

## Gotchas

- **pandoc parses `$`** everywhere in the template, including LaTeX comments.
  A literal dollar in `papers/_lib/paper.latex` must be `$$`, and inline math
  belongs in `\ensuremath{…}`.
- **`$highlighting-macros$` defines `Highlighting` and `Shaded` itself.** Any
  override of those environments must come *after* it in the template or it is
  silently discarded — that is what makes long code lines wrap.
- Requires `pandoc` and `pdflatex` (`brew install pandoc texlive`).
