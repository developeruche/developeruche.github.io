# CV

The CV is written in LaTeX and compiled to a PDF that the site serves at
**`/cv`** — hitting that URL downloads the file.

```
cv/cv.tex                              ← the source you edit
cv/index.html                          ← the /cv route (auto-downloads the PDF)
cv/preview.html                        ← live preview while editing
assets/cv/nwele-uchenna-david-cv.pdf   ← build output (committed; this is what ships)
```

## Live editing

```bash
./cv/dev.sh
```

That starts a static server on `:8000` and a watcher on `cv.tex`. Open
<http://localhost:8000/cv/preview.html>, then edit `cv/cv.tex` — each save
recompiles and the preview refreshes itself within about a second.

The status pill in the preview's top bar shows the state of the last build. If
a compile fails, the LaTeX errors appear over the PDF and the **last good
render stays on screen**, so a typo never leaves you staring at a blank pane.

Already running a server on `:8000`? `dev.sh` reuses it. Use another port with
`PORT=9000 ./cv/dev.sh`.

## One-off build

```bash
./cv/build.sh
```

Compiles and refreshes `assets/cv/nwele-uchenna-david-cv.pdf`. A failed build
leaves the previously published PDF untouched, so `/cv` never serves a broken
file. Aux files stay in `cv/.build/` (gitignored).

## Requirements

`pdflatex`, from TeX Live:

```bash
brew install texlive
```

## Notes on the source

- **Phone number** — `\myphone` near the top of `cv.tex` is defined but empty.
  Fill in the braces to print it in the header; left empty, the slot collapses.
- **Don't add `\usepackage[T1]{fontenc}`.** The comment in `cv.tex` explains
  why: it breaks `fi`/`fl`/`ff` ligature extraction and garbles words for ATS
  résumé parsers. The `glyphtounicode` block right below it is what keeps the
  PDF's text layer clean.

## Shipping a new version

`assets/cv/nwele-uchenna-david-cv.pdf` is committed to the repo — GitHub Pages
serves it directly. After editing, run a build and commit **both** the `.tex`
and the regenerated `.pdf`.
