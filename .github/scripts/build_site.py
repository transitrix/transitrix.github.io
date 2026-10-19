#!/usr/bin/env python3
"""Build a static consumer artifact without changing deployment."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit
from check_publish_manifest import parse_manifest


def consumer_paths(root):
    text = (root / "MANIFEST.md").read_text()
    start = "## Consumer artifact\n"
    end = "## Repository-only files\n"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("Invalid consumer declaration")
    section = text.split(start, 1)[1].split(end, 1)[0]
    return parse_manifest(section)


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src", "poster"):
            if key in attrs:
                self.urls.append(attrs[key])
        if tag == "meta" and attrs.get("property") in ("og:image", "og:url"):
            self.urls.append(attrs.get("content", ""))


def verify_links(output):
    for source in output.rglob("*"):
        if source.suffix not in (".html", ".css"):
            continue
        text = source.read_text()
        if source.suffix == ".html":
            parser = References()
            parser.feed(text)
            refs = parser.urls + re.findall(r'<!--#include virtual="([^"]+)"', text)
        else:
            refs = re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", text)
        for ref in refs:
            url = urlsplit(ref)
            if not url.path or url.scheme not in ("", "http", "https"):
                continue
            if url.netloc and url.netloc not in ("transitrix.com", "www.transitrix.com"):
                continue
            path = unquote(url.path)
            target = output / path.lstrip("/") if path.startswith("/") else source.parent / path
            target = target.resolve()
            if output.resolve() not in target.parents and target != output.resolve():
                raise ValueError("Invalid local reference")
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                raise ValueError("Missing local reference: " + str(source.relative_to(output)) + " -> " + path)


def build(root, output):
    root = root.resolve()
    paths = consumer_paths(root)
    if output.exists():
        raise ValueError("Output path already exists")
    # Validate before writing. Symlinks cannot add files outside the declaration.
    for path in paths:
        source = root / path
        if not source.is_file() or any(parent.is_symlink() for parent in [source, *source.parents]):
            raise ValueError("Invalid consumer path: " + path)
    output.mkdir(parents=True)
    for path in sorted(paths):
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / path, target)
    actual = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
    if actual != paths:
        raise ValueError("Consumer artifact differs from declaration")
    verify_links(output)
    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = build(Path.cwd(), args.output)
    print(f"Consumer artifact passed: {len(paths)} files")
