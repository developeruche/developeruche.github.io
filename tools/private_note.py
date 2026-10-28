#!/usr/bin/env python3
"""
Publish a passphrase-protected note: markdown -> encrypted page at /private/<slug>/.

    python3 tools/private_note.py --md data/private-md/<slug>.md \
        --slug <slug> --title "..." --excerpt "..." [--tags "A, B"] [--date YYYY-MM-DD]
    python3 tools/private_note.py --index-only   # rebuild /private/ alone

The passphrase comes from $PRIVATE_NOTE_PASSPHRASE, else the gitignored file
.private-note-passphrase at the site root, else a prompt (asked twice).

The repo is public and GitHub Pages serves every file, so the only thing that
keeps a note private is encryption. The rendered article (title included) is
encrypted with AES-256-GCM under a key derived by PBKDF2-SHA256 from the
passphrase; the page decrypts it in the browser with WebCrypto. What ships:

  - private/<slug>/index.html   ciphertext + unlock form; noindex, no canonical,
                                so sitemap regeneration skips it
  - private/index.html          the encrypted index of every private note
  - nothing else: no notes.json entry, no sitemap/feed entry, no public links

The markdown sources and the index manifest (data/private-md/notes.json) live in
data/private-md/, which is gitignored. Keep them: re-running this script is the
only way to edit a note or change the passphrase.

Every page uses one fixed salt, so one passphrase derives one key. The browser
keeps that key for the session (or on the device, if asked), so unlocking the
index also unlocks the notes it links to. A per-site salt still defeats
precomputed tables; a fresh random IV per page keeps AES-GCM safe.

Body conversion reuses add-blog's md_to_body.py so the note renders like every
other note. KaTeX is not loaded; private notes are plain prose and tables.
"""
import argparse, base64, datetime, getpass, html, json, os, re, secrets, subprocess, sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROOT = Path(__file__).resolve().parents[1]
CONVERTER = ROOT / ".claude/skills/add-blog/scripts/md_to_body.py"
TEMPLATE = ROOT / "tools/private-note.html.template"
PASSPHRASE_FILE = ROOT / ".private-note-passphrase"  # gitignored
MANIFEST = ROOT / "data/private-md/notes.json"        # gitignored
SALT = b"developeruche.com/private/v1"
ITERATIONS = 600_000  # OWASP 2023 guidance for PBKDF2-HMAC-SHA256
MIN_PASSPHRASE = 12


def read_passphrase():
    p = os.environ.get("PRIVATE_NOTE_PASSPHRASE")
    if p is None and PASSPHRASE_FILE.is_file():
        p = PASSPHRASE_FILE.read_text().strip()
    if p is None:
        p = getpass.getpass("Passphrase: ")
        if getpass.getpass("Repeat passphrase: ") != p:
            sys.exit("error: passphrases differ")
    if len(p) < MIN_PASSPHRASE:
        sys.exit(f"error: passphrase must be at least {MIN_PASSPHRASE} characters; "
                 "the ciphertext is public, so it can be attacked offline")
    return p


e = lambda s: html.escape(str(s), quote=True)


def encrypt_page(key, slug, title, article_html, dest):
    """Encrypt the article and write it into the unlock template at dest."""
    plaintext = json.dumps({"title": title, "html": article_html}, ensure_ascii=False).encode()
    iv = secrets.token_bytes(12)
    ct = AESGCM(key).encrypt(iv, plaintext, None)
    b64 = lambda b: base64.b64encode(b).decode()
    payload = json.dumps({"v": 2, "id": slug, "iter": ITERATIONS,
                          "salt": b64(SALT), "iv": b64(iv), "ct": b64(ct)})
    page = TEMPLATE.read_text().replace("{{PAYLOAD}}", payload)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page)
    print(f"✓ {dest.relative_to(ROOT)}  ({len(page):,} bytes)")


def tags_html(tags):
    return "".join(f"<span>{e(t)}</span>" for t in tags)


def build_index(key, notes):
    cards = "".join(
        '<article class="info-card card card--featured card--no-media"><div class="card-body">'
        f'<h3 class="card-title">{e(n["title"])}</h3>'
        + (f'<div class="meta-tags">{tags_html(n["tags"])}</div>' if n["tags"] else "")
        + f'<p class="card-copy"><time datetime="{n["date"]}">{n["date"]}</time>'
        + (f' · {e(n["excerpt"])}' if n.get("excerpt") else "") + '</p>'
        f'<div class="card-links"><a class="btn-secondary btn-sm" href="/private/{n["slug"]}/">'
        'READ NOTE<span aria-hidden="true"> →</span></a></div>'
        '</div></article>'
        for n in notes)
    article = (
        '<header>\n'
        '  <span class="section-label">// PRIVATE NOTES</span>\n'
        '  <h1 class="post-title">Private Notes</h1>\n'
        f'  <p class="post-meta">// {len(notes)} note{"s" if len(notes) != 1 else ""}, newest first</p>\n'
        '</header>\n'
        f'<div class="card-grid card-grid--list" style="margin-top: var(--space-lg);">{cards}</div>\n'
    )
    encrypt_page(key, "index", "Private Notes", article, ROOT / "private/index.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    ap.add_argument("--slug")
    ap.add_argument("--title")
    ap.add_argument("--excerpt", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--index-only", action="store_true")
    a = ap.parse_args()

    notes = json.loads(MANIFEST.read_text()) if MANIFEST.is_file() else []
    if a.index_only:
        key = derive(read_passphrase())
        build_index(key, notes)
        return
    if not (a.md and a.slug and a.title):
        sys.exit("error: --md, --slug and --title are required (or pass --index-only)")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.slug):
        sys.exit(f"error: slug must be lowercase-kebab-case, got {a.slug!r}")
    src = Path(a.md)
    if not src.is_file():
        sys.exit(f"error: markdown not found: {src}")
    key = derive(read_passphrase())

    body = subprocess.run([sys.executable, str(CONVERTER), str(src)],
                          capture_output=True, text=True, check=True).stdout
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    article = (
        '<a class="back-link" href="/private/">← All private notes</a>\n'
        '<header>\n'
        '  <span class="section-label">// PRIVATE NOTE</span>\n'
        f'  <h1 class="post-title">{e(a.title)}</h1>\n'
        f'  <p class="post-meta">// <span rel="author">Developer Uche</span> · '
        f'<time datetime="{a.date}">{a.date}</time></p>\n'
        + (f'  <div class="meta-tags" style="margin-top: var(--space-sm);">{tags_html(tags)}</div>\n'
           if tags else '')
        + '</header>\n'
        f'<div class="post-body">\n{body}</div>\n'
    )
    encrypt_page(key, a.slug, a.title, article, ROOT / "private" / a.slug / "index.html")

    # --- manifest (upsert, newest first) + index ---------------------------
    notes = [n for n in notes if n["slug"] != a.slug]
    notes.append({"slug": a.slug, "title": a.title, "date": a.date,
                  "excerpt": a.excerpt, "tags": tags, "md": str(src)})
    notes.sort(key=lambda n: n["date"], reverse=True)
    MANIFEST.write_text(json.dumps(notes, indent=2, ensure_ascii=False) + "\n")
    build_index(key, notes)


def derive(passphrase):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT,
                      iterations=ITERATIONS).derive(passphrase.encode())


if __name__ == "__main__":
    main()
