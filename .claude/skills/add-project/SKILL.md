---
name: add-project
description: Add a new project (open-source contribution or personal project) to developeruche.github.io. Upserts an entry into data/os-n-projects.json from a GitHub repo URL (auto-filling name, description, type, links, and suggested tags via the gh CLI) or from explicit details. Projects are pure data — no HTML page or thumbnail is generated. Use when the user wants to add/publish a project, list a repo on the Projects page, or wire a GitHub project into the site.
---

# Add Project

Adds a project card to the **Projects** page of developeruche.github.io. Unlike
blog posts, projects are **100% data-driven**: `projects.html` +
`assets/js/projects.js` read `data/os-n-projects.json` and render cards with
`noMedia: true`. So there is **no HTML page and no thumbnail** to generate — the
whole task is upserting one JSON entry.

## Data model
Each entry in `data/os-n-projects.json`:
```json
{
  "name": "Witnet",
  "type": "personal",                // "personal" | "contribution"
  "description": "One or two sentences.",
  "tags": ["Rust", "Networking"],
  "links": [{ "label": "SOURCE CODE", "url": "https://github.com/..." }],
  "highlight": true,
  "thumbnail": null                   // always null — projects render no media
}
```
- **type** decides the section: `contribution` → "Open Source" grid, `personal`
  → "Personal Projects" grid (filtered by `p.type` in `projects.js`).
- **links** convention in the existing data:
  - `personal` → `{ "label": "SOURCE CODE", "url": <repo url> }`
  - `contribution` → `{ "label": "VIEW PRs", "url": "<repo>/commits?author=developeruche" }`
  - extra links are fine (e.g. `{ "label": "CRATES.IO", "url": "..." }`).

## Inputs to collect
- **Repo** — a GitHub URL (or `owner/repo`). Strongly preferred: the script
  auto-fills name, description, type, links, and suggests tags. If no repo,
  supply `--name`, `--type`, `--description`, `--tags`, and a `--link`.
- **Tags** — 2–4 tags. Reuse the site's existing vocabulary; inspect it first:
  ```bash
  python3 -c "import json;print(sorted({t for p in json.load(open('data/os-n-projects.json')) for t in p['tags']}))"
  ```
  Examples in use: `Rust`, `Ethereum`, `EVM`, `zkVM`, `Zero-Knowledge`, `Smart
  Contract`, `Protocol`, `Layer 2`, `library`, `SDK`, `CLI`, `Indexer`,
  `Architecture`, `Experiment`, `DEX`, `Payments`. Match their casing.
- **Highlight** — `true`/`false` (whether it's featured). Default `true`,
  matching the rest of the list.

## Workflow
Run from the **site root**
(`/Users/gregg/Documents/projects/PROJECTS/developeruche.github.io`).

### 1. Run the script
```bash
python3 .claude/skills/add-project/scripts/new_project.py \
  --repo https://github.com/developeruche/witnet \
  --tags "Rust, Networking, zkVM" \
  --highlight true \
  --root "$(pwd)"
```
- `--type` is auto-detected from the owner (`developeruche` → `personal`, else
  `contribution`); override with `--type` for a contribution to someone else's
  repo that you happen to own a fork of, etc.
- Omit `--tags` to accept the auto-suggested ones (primary language + topics),
  but prefer passing tags that match the site vocabulary.
- Add extra links with repeatable `--link "CRATES.IO=https://crates.io/..."`.
- The script needs the `gh` CLI authenticated; it falls back to the public
  GitHub API if `gh` is unavailable.

It **upserts by name** (idempotent — re-running with the same name replaces that
entry) and inserts new projects at the top of the file (newest first within
their section). It prints the final entry as JSON — confirm `type`, `links`,
`description`, and `tags` look right.

### 2. Verify
```bash
python3 -c "import json;d=json.load(open('data/os-n-projects.json'));print([p['name'] for p in d][:5])"
```
Then serve with the `static` preview config and open `/projects.html`; confirm
the new card shows in the correct section, the tag filter includes its tags, and
the link(s) resolve. Check the console for errors. (No page/sitemap changes are
needed — projects are not standalone pages.)

## Gotchas
- **No page, no thumbnail, no sitemap entry** — projects differ from blogs here.
  Keep `thumbnail: null`.
- The Projects page reads the JSON at runtime; there's no build step. A malformed
  JSON entry breaks the whole grid, so let the script write the file (valid JSON)
  rather than hand-editing.
- Descriptions read best at 1–2 sentences. If the repo's GitHub description is
  long or empty, pass a tightened `--description`.
- For contributions, the default link points at your commits
  (`/commits?author=developeruche`) — adjust with `--link` if you want to link
  the repo or a specific PR set instead.
