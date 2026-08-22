#!/usr/bin/env python3
"""Render one library item's committed source to a PDF via headless Chrome.

Usage: python3 scripts/render_library_item.py <slug>

Reads library/<slug>/<slug>.source.html, renders it offline (a local server on
127.0.0.1 only — no third-party network fetch) and writes library/<slug>/<slug>.pdf
beside it. The script never edits the source; it only reads and renders.

Page geometry is taken from the source's own `@page { size: <w>mm <h>mm }` rule
and asserted against the rendered PDF's MediaBox (see check_library.py for the
committed-tree guard; this script only asserts what it itself produced).
"""
import http.server
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

GEOMETRY_TOLERANCE_PT = 0.5

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "google-chrome",
    "chromium",
]


def find_chrome():
    for candidate in CHROME_CANDIDATES:
        if os.path.isabs(candidate):
            if os.path.isfile(candidate):
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    raise SystemExit("render_library_item: no Chrome/Chromium binary found")


def chrome_version(chrome_path):
    """Never shells out to Chrome for this: `--version` talks to an already-running
    instance instead of printing and exiting ("Opening in existing browser session."),
    and an isolated `--headless=new` instance observed on this host does not print a
    version at all - it starts a full (headless) browser and sits there. The file's own
    version resource is what every other consumer of "the Chrome version" (Explorer's
    Properties dialog, package managers) reads, and reading it never launches a process.
    """
    if sys.platform == "win32":
        ps_literal_path = chrome_path.replace("'", "''")
        out = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                f"(Get-Item -LiteralPath '{ps_literal_path}').VersionInfo.ProductVersion",
            ],
            capture_output=True, text=True, check=True, timeout=15,
        )
        version = out.stdout.strip()
        if not version:
            raise SystemExit(f"render_library_item: could not read a version from {chrome_path}")
        return f"Google Chrome {version}"
    out = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, check=True, timeout=15)
    return out.stdout.strip()


def page_size_mm(source_path):
    """Parse `@page { size: <w>mm <h>mm; ... }` out of the source's own CSS."""
    with open(source_path, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"@page\s*\{[^}]*size:\s*([\d.]+)mm\s+([\d.]+)mm", html)
    if not m:
        raise SystemExit(f"render_library_item: {source_path} has no `@page {{ size: <w>mm <h>mm }}` rule")
    return float(m.group(1)), float(m.group(2))


def mm_to_pt(mm):
    return mm * 72.0 / 25.4


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def serve_repo_root(repo_root):
    """Starts a 127.0.0.1-only static server rooted at the repo root, so a
    source's absolute paths (/assets/...) resolve the same way they will once
    published. Returns (server, thread, port)."""
    handler = lambda *a, **kw: _QuietHandler(*a, directory=repo_root, **kw)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def render_pdf(chrome_path, url, out_path):
    with tempfile.TemporaryDirectory(prefix="render-library-item-") as profile_dir:
        cmd = [
            chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={profile_dir}",
            "--disable-sync",
            "--disable-extensions",
            "--disable-default-apps",
            "--disable-background-networking",
            "--virtual-time-budget=4000",
            f"--print-to-pdf={out_path}",
            "--no-pdf-header-footer",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0 or not os.path.isfile(out_path):
            raise SystemExit(
                f"render_library_item: Chrome render failed (exit {result.returncode})\n{result.stderr}"
            )


def read_mediabox_and_page_count(pdf_path):
    with open(pdf_path, "rb") as f:
        data = f.read()
    boxes = re.findall(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]", data)
    if not boxes:
        raise SystemExit(f"render_library_item: {pdf_path} carries no /MediaBox")
    page_count = len(re.findall(rb"/Type\s*/Page[^s]", data))
    w = float(boxes[0][2]) - float(boxes[0][0])
    h = float(boxes[0][3]) - float(boxes[0][1])
    return w, h, page_count


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: render_library_item.py <slug>")
    slug = sys.argv[1]

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    item_dir = os.path.join(repo_root, "library", slug)
    source_path = os.path.join(item_dir, f"{slug}.source.html")
    out_path = os.path.join(item_dir, f"{slug}.pdf")

    if not os.path.isfile(source_path):
        raise SystemExit(f"render_library_item: no source at {source_path}")

    want_w_mm, want_h_mm = page_size_mm(source_path)
    want_w_pt, want_h_pt = mm_to_pt(want_w_mm), mm_to_pt(want_h_mm)

    chrome_path = find_chrome()
    print(f"render_library_item: using {chrome_version(chrome_path)}")

    server, thread, port = serve_repo_root(repo_root)
    try:
        url = f"http://127.0.0.1:{port}/library/{slug}/{slug}.source.html"
        render_pdf(chrome_path, url, out_path)
    finally:
        server.shutdown()
        thread.join(timeout=5)

    got_w_pt, got_h_pt, page_count = read_mediabox_and_page_count(out_path)

    if page_count != 1:
        raise SystemExit(f"render_library_item: expected exactly 1 page, got {page_count}")
    if abs(got_w_pt - want_w_pt) > GEOMETRY_TOLERANCE_PT or abs(got_h_pt - want_h_pt) > GEOMETRY_TOLERANCE_PT:
        raise SystemExit(
            "render_library_item: rendered MediaBox "
            f"{got_w_pt:.2f}x{got_h_pt:.2f}pt does not match the source's @page size "
            f"{want_w_pt:.2f}x{want_h_pt:.2f}pt (tolerance {GEOMETRY_TOLERANCE_PT}pt)"
        )

    print(
        f"render_library_item: {slug} -> {out_path} "
        f"({got_w_pt:.2f}x{got_h_pt:.2f}pt, 1 page, geometry asserted from the source's own @page rule)"
    )


if __name__ == "__main__":
    main()
