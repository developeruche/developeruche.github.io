# Running the Site

This is a **static** site — vanilla HTML, CSS, and JS with **no build step**.
It must be served over HTTP (not opened via `file://`) because the pages use
`fetch()` and ES modules, which browsers block on the `file://` protocol.

## Quick start

Pick any one of these from the project root. Then open the printed URL
(e.g. <http://localhost:8000>) in a browser.

### Python 3

```bash
python3 -m http.server 8000
```

### Node (http-server)

```bash
npx -y http-server -p 8000 -c-1
```

> `-c-1` disables caching so edits show up on reload.

### VS Code

Install the **Live Server** extension, then right-click `index.html` →
**Open with Live Server**.

## Pages

| URL | File | What it shows |
| --- | --- | --- |
| `/` or `/index.html` | `index.html` | Home: hero, companies strip, 4 highlight sections |
| `/projects.html` | `projects.html` | Open-source + personal projects, filterable |
| `/blog.html` | `blog.html` | All blog posts (cards open the external source) |
| `/publications.html` | `publications.html` | Research papers + publications |
| `/blog-post.html` | `blog-post.html` | Dummy post detail template (not yet linked) |
| `/cv` | `cv/index.html` | Downloads the CV PDF (auto-starts on load) |
| `/cv/preview.html` | `cv/preview.html` | Live LaTeX preview — dev only, `noindex` |

Filtered views are shareable via query string, e.g.
`/projects.html?tags=rust,evm`.

## Editing content

All content lists are **data-driven** — adding or editing entries needs **no
code change**. Edit the JSON in `data/` and reload:

- `data/publications.json`
- `data/blog.json`
- `data/os-n-projects.json`
- `data/companies.json` — hero "companies I've worked with" strip
  (currently empty placeholder slots; add `{ "name": "...", "logo": "assets/..." }`)

Notes:
- **Tags** are matched case-insensitively and shown in Title Case, so
  `rust`, `Rust`, and `RUST` are treated as the same tag.
- **`highlight: true`** controls which items appear in the home-page highlight
  sections (first 4 of each). See the `// TODO: curate highlights` note in
  `assets/js/home.js`.
- **`thumbnail: null`** renders an animated blueprint skeleton placeholder;
  set a URL to render a real image instead.
- Toggle `FILTER_MODE` in `assets/js/data.js` between `'OR'` (default) and
  `'AND'` to change how multiple selected tags combine.

## Editing the CV

The CV is LaTeX, compiled to `assets/cv/nwele-uchenna-david-cv.pdf` — the file
`/cv` hands out. It needs `pdflatex` (`brew install texlive`).

```bash
./cv/dev.sh
```

Starts a server **and** a watcher on `cv/cv.tex`; open
<http://localhost:8000/cv/preview.html> and every save recompiles and refreshes
the preview. `./cv/build.sh` does a single build. Full notes in
[`cv/README.md`](cv/README.md).

Commit the regenerated PDF along with the `.tex` — Pages serves it as a static
file, so an un-rebuilt PDF means a stale `/cv`.

## Deploying

It's already structured for **GitHub Pages** at the repo root. Push to the
branch configured under repo **Settings → Pages** (the `CNAME` file points the
custom domain). All paths are relative, so no extra configuration is needed.
