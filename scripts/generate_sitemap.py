#!/usr/bin/env python3
"""Generate sitemap.xml from the set of indexable pages in this repository.

A page is indexable if it has an index.html and that file does not carry
<meta name="robots" content="noindex">. English/German mirrors are paired by
path (e.g. /install/ <-> /de/install/) for hreflang alternates.

Usage: python3 scripts/generate_sitemap.py > sitemap.xml

CI (.github/workflows/indexing-declarations.yml) runs this script and fails
if its output does not match the committed sitemap.xml, so a page added or
removed without regenerating the file is caught rather than silently absent.
"""
import os
import re
import sys

ORIGIN = "https://transitrix.com"
EXCLUDE_DIRS = {".git", ".github", "assets", "node_modules"}
NOINDEX_RE = re.compile(r'<meta\s+name="robots"\s+content="[^"]*noindex[^"]*"')


def find_pages(root):
    pages = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
        if "index.html" not in filenames:
            continue
        rel_dir = os.path.relpath(dirpath, root)
        url_path = "/" if rel_dir == "." else "/" + rel_dir.replace(os.sep, "/") + "/"
        file_path = os.path.join(dirpath, "index.html")
        with open(file_path, encoding="utf-8") as f:
            html = f.read()
        if NOINDEX_RE.search(html):
            continue
        pages.append(url_path)
    return sorted(pages)


def lang_of(url_path):
    return "de" if url_path.startswith("/de/") else "en"


def mirror_of(url_path):
    if url_path == "/":
        return "/de/"
    if url_path == "/de/":
        return "/"
    if url_path.startswith("/de/"):
        return "/" + url_path[len("/de/"):]
    return "/de/" + url_path[1:]


def find_library_pdfs(root):
    pdfs = []
    library_dir = os.path.join(root, "library")
    if not os.path.isdir(library_dir):
        return pdfs
    for slug in sorted(os.listdir(library_dir)):
        slug_dir = os.path.join(library_dir, slug)
        if not os.path.isdir(slug_dir) or slug in EXCLUDE_DIRS or slug.startswith("."):
            continue
        index_file = os.path.join(slug_dir, "index.html")
        pdf_file = os.path.join(slug_dir, f"{slug}.pdf")
        if os.path.isfile(index_file) and os.path.isfile(pdf_file):
            pdfs.append(f"/library/{slug}/{slug}.pdf")
    return pdfs


def build_sitemap(root):
    pages = find_pages(root)
    page_set = set(pages)
    en_pages = [p for p in pages if lang_of(p) == "en"]
    de_pages = [p for p in pages if lang_of(p) == "de"]
    pdfs = find_library_pdfs(root)

    def emit_page(lines, url_path):
        lang = lang_of(url_path)
        mirror = mirror_of(url_path)
        lines.append("  <url>")
        lines.append(f"    <loc>{ORIGIN}{url_path}</loc>")
        lines.append(f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{ORIGIN}{url_path}"/>')
        if mirror in page_set:
            other_lang = lang_of(mirror)
            lines.append(f'    <xhtml:link rel="alternate" hreflang="{other_lang}" href="{ORIGIN}{mirror}"/>')
        lines.append("  </url>")

    def emit_pdf(lines, url_path):
        lines.append("  <url>")
        lines.append(f"    <loc>{ORIGIN}{url_path}</loc>")
        lines.append("  </url>")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        "",
    ]
    for p in en_pages:
        emit_page(lines, p)
    for pdf in pdfs:
        emit_pdf(lines, pdf)
    lines.append("")
    for p in de_pages:
        emit_page(lines, p)
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.stdout.write(build_sitemap(repo_root))
