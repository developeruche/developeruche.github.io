# Papers

Research papers are written in **markdown** and compiled to a typeset PDF that
the site serves at `/publications/<slug>/`.

```
papers/<slug>/paper.md            ← what you edit
papers/<slug>/meta.json           ← title, authors, date, abstract, tags, links
papers/_lib/paper.latex           ← the academic LaTeX template (shared)
assets/papers/<slug>.pdf          ← build output (committed; this is what ships)
publications/<slug>/index.html    ← the public detail page (generated)
```

## Live editing

```bash
./papers/dev.sh <slug>
```

Starts a static server and a watcher. Open
<http://localhost:8000/papers/preview.html> — every save of `paper.md` or
`meta.json` recompiles and the preview refreshes within about a second.

The status pill shows the last build. If LaTeX fails, the errors appear over
the PDF and the **last good render stays on screen**, so a typo never leaves
you staring at a blank pane. Omit the slug to watch every paper; the preview's
dropdown switches between them.

## One-off build

```bash
./papers/build.sh <slug>     # or --all
```

A failed build leaves the published PDF untouched. Intermediates stay in
`papers/<slug>/.build/` (gitignored).

## After editing

The detail page embeds metadata (title, abstract, tags) at generate time, so
re-render it whenever `meta.json` or the publications entry changes:

```bash
python3 .claude/skills/add-paper/scripts/render_publication.py <slug>
```

## Adding a new paper

Use the `add-paper` skill — it handles the markdown normalisation, the
`data/publications.json` entry, the detail page, and the sitemap. See
`.claude/skills/add-paper/SKILL.md`.

## Requirements

```bash
brew install pandoc texlive
```

## Template notes

`_lib/paper.latex` is a **pandoc** template, so `$` is pandoc syntax even
inside LaTeX comments — write a literal dollar as `$$` and inline math as
`\ensuremath{…}`. Overrides of the `Highlighting`/`Shaded` environments must
come after `$highlighting-macros$`, which defines them; that ordering is what
makes long code lines wrap instead of running off the page.
