#!/usr/bin/env python3
"""
Static dev server that resolves URLs the way GitHub Pages does.

    python3 serve.py [port]        # default 8000

Plain `python3 -m http.server` serves files literally, so /projects returns 404
even though GitHub Pages serves it from projects.html. Site links are
extensionless, so previewing locally needs the same resolution order Pages uses:

    /path        -> path                (exact file)
                 -> path/index.html     (directory index)
                 -> path.html           (extensionless page)

Anything still unresolved falls through to the normal 404.
"""
import http.server
import os
import posixpath
import sys
from urllib.parse import urlsplit


class PagesHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = super().translate_path(path)
        url_path = urlsplit(path).path

        if os.path.isdir(local):
            if os.path.isfile(os.path.join(local, "index.html")):
                return local  # base class appends index.html itself
            # A directory with no index. Pages falls back to the sibling page,
            # which is how /blog serves blog.html while blog/<slug>/ pages also
            # exist. Only without a trailing slash: Pages 404s on "/blog/".
            if not url_path.endswith("/"):
                sibling = local.rstrip("/\\") + ".html"
                if os.path.isfile(sibling):
                    return sibling
            return local

        if os.path.exists(local):
            return local

        # Not found literally: try the extensionless form, as Pages does.
        if not posixpath.splitext(url_path)[1]:
            candidate = local.rstrip("/\\") + ".html"
            if os.path.isfile(candidate):
                return candidate
        return local

    def list_directory(self, path):
        # Pages serves no directory indexes; a directory without index.html
        # is a 404 there, so don't let it look browsable here.
        self.send_error(404, "No permission to list directory")
        return None

    def end_headers(self):
        # Never cache during development, so edits show up on reload.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), PagesHandler)
    print(f"serving {os.getcwd()} on http://localhost:{port} (Pages-style URLs)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
