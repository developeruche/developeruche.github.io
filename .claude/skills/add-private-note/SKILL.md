---
name: add-private-note
description: Publish a private, passphrase-protected note to developeruche.github.io from markdown. Encrypts the rendered note (AES-256-GCM, decrypted in the browser) into /private/<slug>/, plus an encrypted index at /private/, unlisted and noindex, with the markdown source kept local and gitignored. Use when the user wants to add a private note, a hidden/locked/password-protected note, or private material such as AI summaries of calls.
---

# Add Private Note

The repo is **public** and GitHub Pages serves every file, so a private note is
**encrypted**, not merely hidden. Do not use `add-note` / `new_note.py` for these.

What it produces:
- `private/<slug>/index.html` — ciphertext plus an unlock form, served at
  `/private/<slug>/`. The title is encrypted too. It is `noindex`, has no
  canonical, and is **not** added to notes.json, the sitemap, the feed or the
  home page. Nothing links to it.
- `private/index.html` — the **encrypted index** at `/private/`, which lists every
  private note newest first. It is rebuilt on every run.
- `data/private-md/<slug>.md` — the source, and `data/private-md/notes.json` —
  the index manifest (slug, title, date, excerpt, tags). **Both are gitignored;
  never commit them.**

## Passphrase

The site-wide private-note passphrase is stored in the gitignored file
`.private-note-passphrase` at the site root, and the script reads it
automatically. Never commit that file, and never put the passphrase in a
committed file. If the file is missing, ask the user for the passphrase. Don't
invent a new one, or their existing notes and new ones end up with different
passphrases.

## Workflow

Run from the site root.

1. Save the markdown to `data/private-md/<slug>.md`, then clean it:
   - Remove the `# Title` line (the page renders the title), plus any byline or
     date line under it.
   - Remove export leftovers such as `&#91;embedded content: …]` placeholders.
   - Fix `~~x (~~y` artifacts. Google Docs exports `~` as strikethrough
     markers, and they should read `\~x (\~y`.
2. Encrypt:
   ```bash
   python3 tools/private_note.py --md data/private-md/<slug>.md --slug <slug> \
     --title "..." --excerpt "One sentence for the index card." \
     --tags "A, B" [--date YYYY-MM-DD]
   ```
   Always write an `--excerpt`: it is the only summary on the index card.
   `python3 tools/private_note.py --index-only` rebuilds just the index, for
   example after hand-editing the manifest to remove a note. When you remove a
   note, also delete its `private/<slug>/` folder.
   `--date` defaults to today. Use the document's own date if it states one.
   Don't infer a date from git history.
3. Verify:
   - `grep` the output for a distinctive phrase from the note, and
     `private/index.html` for its title. Both must find **nothing**, because the
     pages should hold only ciphertext.
   - Open `/private/` with the `static` preview and unlock it. The new note
     should be listed. Click through: the note must open **without** asking
     again, since the key is shared for the session. Check its headings,
     tables and checkboxes, and that the console is clean.
   - Clear `localStorage` and `sessionStorage` afterwards.
4. Skip the SEO pass. Private notes must stay out of `data/seo.json`.

Re-running the script is how you edit a note or re-key it. To change the
passphrase for every note, update `.private-note-passphrase`, then re-run the
script for each entry in `data/private-md/notes.json`, using its stored `md`,
title, date, excerpt and tags. Every page must be re-keyed together, because
they share one key.

## Notes
- Body conversion reuses `add-blog/scripts/md_to_body.py`. KaTeX is not loaded,
  so private notes should be prose, tables and lists.
- Encryption uses PBKDF2-SHA256 (600k iterations) and AES-256-GCM, through
  WebCrypto in the page and `cryptography` in Python.
- Every page uses a fixed per-site salt (`SALT` in the script), so the
  passphrase derives a single key. After one unlock, that key stays in
  `sessionStorage` for the tab session. "Remember on this device" also puts it
  in `localStorage`. "Lock private notes" clears both.
