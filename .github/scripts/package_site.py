#!/usr/bin/env python3
"""Create and verify a Pages tar without dropping dot paths."""
import argparse
import hashlib
import io
from pathlib import Path
import tarfile
from build_site import consumer_paths


def verify_archive(root, archive):
    expected = consumer_paths(root)
    directories = {"."} | {str(parent) for path in expected for parent in Path(path).parents}
    seen = set()
    seen_directories = set()
    with tarfile.open(archive, "r:") as tar:
        for member in tar:
            path = member.name[2:] if member.name.startswith("./") else member.name
            if path != "." and (path.startswith("/") or any(part in ("", ".", "..") for part in path.split("/"))):
                raise ValueError("Invalid Pages archive path: " + member.name)
            if member.isdir():
                if path not in directories or path in seen_directories:
                    raise ValueError("Invalid Pages archive directory: " + member.name)
                seen_directories.add(path)
                continue
            if not member.isfile() or path not in expected or path in seen:
                raise ValueError("Invalid Pages archive path: " + member.name)
            data = tar.extractfile(member).read()
            if hashlib.sha256(data).digest() != hashlib.sha256((root / path).read_bytes()).digest():
                raise ValueError("Pages archive content differs: " + member.name)
            seen.add(path)
    if seen != expected or seen_directories != directories:
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
    directories = {"."} | {str(parent) for path in expected for parent in Path(path).parents}
    # Match `tar -C site -cf artifact.tar .`, used by upload-pages-artifact:
    # root + ancestor directories, ./ paths, GNU headers and real file mtimes.
    with archive.open("xb") as stream, tarfile.open(fileobj=stream, mode="w", format=tarfile.GNU_FORMAT) as tar:
        for path in sorted(directories, key=lambda item: (len(Path(item).parts), item)):
            member = tar.gettarinfo(str(site / path), arcname="." if path == "." else "./" + path)
            member.mode = 0o755
            tar.addfile(member)
        for path in sorted(expected):
            data = (site / path).read_bytes()
            member = tar.gettarinfo(str(site / path), arcname="./" + path)
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
