#!/usr/bin/env python3
"""
new_project.py — add (or update) a project in data/os-n-projects.json for
developeruche.github.io.

Projects are 100% data-driven: projects.html / assets/js/projects.js read this
JSON and render cards (with noMedia: true, so projects have NO thumbnail/page —
unlike blogs). Adding a project therefore just means upserting one JSON entry.

Given a GitHub repo URL it auto-fills sensible defaults via `gh` (falling back to
the public GitHub API):
  - name        : repo name, prettified (override with --name)
  - description : the repo's GitHub description (override with --description)
  - type        : "personal" if the owner is `developeruche`, else "contribution"
  - links       : personal  -> {"SOURCE CODE": <repo url>}
                  contribution -> {"VIEW PRs": <repo>/commits?author=developeruche}
  - tags        : suggested from primary language + topics (override with --tags;
                  passing --tags is recommended so you can match the site's
                  existing tag vocabulary)

Entry shape (matches the existing file):
  { "name", "type", "description", "tags": [...], "links": [{"label","url"}],
    "highlight": bool, "thumbnail": null }

Usage:
  python3 new_project.py --repo https://github.com/developeruche/witnet \
    --tags "Rust, Networking, zkVM" --highlight true --root "$(pwd)"

  # fully manual (no repo lookup):
  python3 new_project.py --name "My Tool" --type personal \
    --description "..." --tags "Rust, CLI" \
    --link "SOURCE CODE=https://github.com/developeruche/my-tool" --root "$(pwd)"

Prints a JSON summary of the upserted entry to stdout.
"""
import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.request

OWNER_SELF = "developeruche"


def run_gh(repo_slug):
    """Return repo metadata dict via `gh`, or None if gh is unavailable/fails."""
    try:
        out = subprocess.run(
            ["gh", "repo", "view", repo_slug, "--json",
             "name,description,primaryLanguage,repositoryTopics,owner"],
            capture_output=True, text=True, timeout=30)
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except Exception:  # noqa: BLE001
        return None


def run_api(repo_slug):
    """Fallback: public GitHub REST API (no auth, rate-limited)."""
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo_slug}",
            headers={"User-Agent": "developeruche-add-project/1.0",
                     "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            d = json.load(r)
        return {
            "name": d.get("name"),
            "description": d.get("description"),
            "primaryLanguage": {"name": d.get("language")} if d.get("language") else None,
            "repositoryTopics": [{"name": t} for t in d.get("topics", [])],
            "owner": {"login": (d.get("owner") or {}).get("login")},
        }
    except Exception as e:  # noqa: BLE001
        print(f"WARN: GitHub API lookup failed: {e}", file=sys.stderr)
        return None


def parse_repo(url):
    """Return (slug 'owner/repo', clean_url) from a GitHub URL or 'owner/repo'."""
    s = url.strip().rstrip("/")
    s = re.sub(r"^https?://github\.com/", "", s)
    s = re.sub(r"\.git$", "", s)
    parts = s.split("/")
    if len(parts) < 2:
        raise SystemExit(f"ERROR: cannot parse repo from {url!r}")
    slug = f"{parts[0]}/{parts[1]}"
    return slug, f"https://github.com/{slug}"


def prettify_name(repo_name):
    """witnet -> Witnet ; my-cool-tool -> My Cool Tool (best-effort; override-able)."""
    words = re.split(r"[-_\s]+", repo_name.strip())
    return " ".join(w[:1].upper() + w[1:] for w in words if w) or repo_name


def suggest_tags(meta):
    tags = []
    pl = (meta.get("primaryLanguage") or {}).get("name")
    if pl:
        tags.append(pl)
    for t in (meta.get("repositoryTopics") or []):
        name = t.get("name") if isinstance(t, dict) else t
        if name:
            tags.append(name.replace("-", " ").title())
    # de-dup, cap at 4
    seen, out = set(), []
    for t in tags:
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out[:4]


def upsert(root, entry):
    path = os.path.join(root, "data", "os-n-projects.json")
    data = json.load(open(path, encoding="utf-8"))
    for i, it in enumerate(data):
        if it.get("name", "").strip().lower() == entry["name"].strip().lower():
            data[i] = entry  # replace in place (idempotent)
            break
    else:
        data.insert(0, entry)  # newest first within its type section
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="GitHub URL or owner/repo (auto-fills fields).")
    ap.add_argument("--name")
    ap.add_argument("--description")
    ap.add_argument("--type", choices=["personal", "contribution"])
    ap.add_argument("--tags", default="", help="Comma-separated; overrides suggestions.")
    ap.add_argument("--link", action="append", default=[],
                    help="Extra link as 'LABEL=URL' (repeatable). If omitted, a "
                         "default link is built from --repo/--type.")
    ap.add_argument("--highlight", default="true")
    ap.add_argument("--root", default=os.getcwd())
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    highlight = str(a.highlight).strip().lower() in ("true", "1", "yes")

    meta, repo_url, owner = {}, None, None
    if a.repo:
        slug, repo_url = parse_repo(a.repo)
        owner = slug.split("/")[0]
        meta = run_gh(slug) or run_api(slug) or {}
        if not meta:
            print("WARN: could not fetch repo metadata; relying on flags.", file=sys.stderr)
        owner = (meta.get("owner") or {}).get("login") or owner

    # type
    ptype = a.type or ("personal" if (owner and owner.lower() == OWNER_SELF) else
                       ("contribution" if owner else None))
    if not ptype:
        raise SystemExit("ERROR: --type is required when --repo is not given.")

    # name
    name = a.name or (prettify_name(meta["name"]) if meta.get("name") else None)
    if not name:
        raise SystemExit("ERROR: --name is required (no repo metadata to derive it).")

    # description
    description = a.description or meta.get("description")
    if not description:
        raise SystemExit("ERROR: --description is required (repo has none).")

    # tags
    if a.tags.strip():
        tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    else:
        tags = suggest_tags(meta)
    if not tags:
        raise SystemExit("ERROR: no tags — pass --tags.")

    # links
    links = []
    for spec in a.link:
        if "=" not in spec:
            raise SystemExit(f"ERROR: --link must be 'LABEL=URL', got {spec!r}")
        label, url = spec.split("=", 1)
        links.append({"label": label.strip(), "url": url.strip()})
    if not links:
        if not repo_url:
            raise SystemExit("ERROR: no links — pass --repo or --link 'LABEL=URL'.")
        if ptype == "personal":
            links = [{"label": "SOURCE CODE", "url": repo_url}]
        else:
            links = [{"label": "VIEW PRs",
                      "url": f"{repo_url}/commits?author={OWNER_SELF}"}]

    entry = {
        "name": name,
        "type": ptype,
        "description": description,
        "tags": tags,
        "links": links,
        "highlight": highlight,
        "thumbnail": None,
    }
    upsert(root, entry)
    print(json.dumps({"upserted": entry,
                      "file": "data/os-n-projects.json"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
