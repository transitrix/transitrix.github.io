#!/usr/bin/env python3
"""Check exact declarations for the complete tracked public repository."""
import json
from pathlib import Path
import re
import subprocess
import sys


def parse_manifest(content):
    paths = re.findall(r"^- `([^`]+)`(?: .*)?$", content, re.MULTILINE)
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Invalid publish manifest")
    for path in paths:
        if (re.search(r"[\\\x00-\x20\x7f*?\[\]]", path)
                or any(part in ("", ".", "..") for part in path.split("/"))):
            raise ValueError("Invalid publish manifest")
    return set(paths)


def main():
    try:
        allowed = parse_manifest(Path("MANIFEST.md").read_text())
        tracked = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
        missing = sorted({path for path in tracked if path and path not in allowed})
        for path in missing:
            print("Undeclared path: " + json.dumps(path), file=sys.stderr)
        if missing:
            return 1
        print("Publish manifest passed")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError):
        print("Publish manifest check failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
