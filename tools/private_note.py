#!/usr/bin/env python3
"""
Publish a passphrase-protected note: markdown -> encrypted page at /private/<slug>/.

    python3 tools/private_note.py --md data/private-md/<slug>.md \
        --slug <slug> --title "..." [--tags "A, B"] [--date YYYY-MM-DD]

The passphrase comes from $PRIVATE_NOTE_PASSPHRASE, else the gitignored file
.private-note-passphrase at the site root, else a prompt (asked twice).

The repo is public and GitHub Pages serves every file, so the only thing that
keeps a note private is encryption. The rendered article (title included) is
encrypted with AES-256-GCM under a key derived by PBKDF2-SHA256 from the
passphrase; the page decrypts it in the browser with WebCrypto. What ships:

  - private/<slug>/index.html   ciphertext + unlock form; noindex, no canonical,
                                so sitemap regeneration skips it
  - nothing else: no notes.json entry, no sitemap/feed entry, no links

The markdown source lives in data/private-md/, which is gitignored. Keep it:
re-running this script is the only way to edit the note or change passphrase.

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--tags", default="")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.slug):
        sys.exit(f"error: slug must be lowercase-kebab-case, got {a.slug!r}")
    src = Path(a.md)
    if not src.is_file():
        sys.exit(f"error: markdown not found: {src}")
    passphrase = read_passphrase()

    body = subprocess.run([sys.executable, str(CONVERTER), str(src)],
                          capture_output=True, text=True, check=True).stdout
    e = lambda s: html.escape(str(s), quote=True)
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    article = (
        '<header>\n'
        '  <span class="section-label">// PRIVATE NOTE</span>\n'
        f'  <h1 class="post-title">{e(a.title)}</h1>\n'
        f'  <p class="post-meta">// <span rel="author">Developer Uche</span> · '
        f'<time datetime="{a.date}">{a.date}</time></p>\n'
        + ('  <div class="meta-tags" style="margin-top: var(--space-sm);">'
           + "".join(f"<span>{e(t)}</span>" for t in tags) + '</div>\n' if tags else '')
        + '</header>\n'
        f'<div class="post-body">\n{body}</div>\n'
    )
    plaintext = json.dumps({"title": a.title, "html": article}, ensure_ascii=False).encode()

    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=ITERATIONS).derive(passphrase.encode())
    ct = AESGCM(key).encrypt(iv, plaintext, None)
    b64 = lambda b: base64.b64encode(b).decode()
    payload = json.dumps({"v": 1, "id": a.slug, "iter": ITERATIONS,
                          "salt": b64(salt), "iv": b64(iv), "ct": b64(ct)})

    page = TEMPLATE.read_text().replace("{{PAYLOAD}}", payload)
    dest = ROOT / "private" / a.slug / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page)
    print(f"✓ private/{a.slug}/index.html  ({len(page):,} bytes, served at /private/{a.slug}/)")


if __name__ == "__main__":
    main()
