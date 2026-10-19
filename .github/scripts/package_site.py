#!/usr/bin/env python3
"""Create and verify the regular-file Pages tar without dropping dot paths."""
import argparse
import hashlib
import io
from pathlib import Path
import tarfile
from build_site import consumer_paths


def verify_archive(root, archive):
    expected = consumer_paths(root)
    seen = set()
    with tarfile.open(archive, "r:") as tar:
        for member in tar:
            if not member.isfile() or member.name not in expected or member.name in seen:
                raise ValueError("Invalid Pages archive path: " + member.name)
            data = tar.extractfile(member).read()
            if hashlib.sha256(data).digest() != hashlib.sha256((root / member.name).read_bytes()).digest():
                raise ValueError("Pages archive content differs: " + member.name)
            seen.add(member.name)
    if seen != expected:
        raise ValueError("Pages archive differs from consumer declaration")
    return seen


def package(root, site, archive):
    expected = consumer_paths(root)
    actual = {str(path.relative_to(site)) for path in site.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError("Consumer directory differs from declaration")
    if archive.exists():
        raise ValueError("Archive path already exists")
    for path in expected:
        source = site / path
        if source.is_symlink() or any(parent.is_symlink() for parent in source.parents if site in parent.parents):
            raise ValueError("Invalid consumer path: " + path)
    with archive.open("xb") as stream, tarfile.open(fileobj=stream, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for path in sorted(expected):
            data = (site / path).read_bytes()
            member = tarfile.TarInfo(path)
            member.size = len(data)
            member.mode = 0o644
            tar.addfile(member, io.BytesIO(data))
    verify_archive(root, archive)
    return expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = package(Path.cwd(), args.site, args.output)
    print(f"Verified Pages archive: {len(paths)} files")
