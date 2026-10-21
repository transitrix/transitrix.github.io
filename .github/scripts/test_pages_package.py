import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from build_site import build
from package_site import package, verify_archive


class PagesPackageTests(unittest.TestCase):
    def test_actual_archive_preserves_all_consumer_bytes_and_dot_paths(self):
        with tempfile.TemporaryDirectory(prefix="pages-package-") as tmp:
            site, archive = Path(tmp) / "site", Path(tmp) / "artifact.tar"
            paths = build(Path.cwd(), site)
            self.assertEqual(package(Path.cwd(), site, archive), paths)
            self.assertIn(".well-known/security.txt", verify_archive(Path.cwd(), archive))
            self.assertIn(".nojekyll", verify_archive(Path.cwd(), archive))
            with tarfile.open(archive) as tar:
                members = tar.getmembers()
                self.assertEqual(members[0].name, ".")
                self.assertTrue(members[0].isdir())
                self.assertEqual(sum(member.isfile() for member in members), len(paths))
                self.assertTrue(all(member.name == "." or member.name.startswith("./") for member in members))
                self.assertTrue(all(member.mtime > 0 for member in members))

    def test_structural_directories_do_not_admit_traversal_extras_aliases_or_links(self):
        for name, kind in (("./../outside", tarfile.DIRTYPE), ("/outside", tarfile.DIRTYPE),
                           ("./unrelated", tarfile.DIRTYPE), ("./index.html", tarfile.DIRTYPE),
                           ("index.html", tarfile.REGTYPE), ("./link", tarfile.SYMTYPE),
                           ("./link", tarfile.LNKTYPE)):
            with self.subTest(name=name, kind=kind), tempfile.TemporaryDirectory(prefix="pages-package-") as tmp:
                root, site, archive = Path.cwd(), Path(tmp) / "site", Path(tmp) / "artifact.tar"
                build(root, site)
                package(root, site, archive)
                with tarfile.open(archive, "a") as tar:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE): member.linkname = "index.html"
                    tar.addfile(member)
                with self.assertRaises(ValueError): verify_archive(root, archive)

    def test_archive_requires_ancestor_directories_and_preserves_hash_checks(self):
        for case in ("missing-directory", "changed-content"):
            with self.subTest(case=case), tempfile.TemporaryDirectory(prefix="pages-package-") as tmp:
                root, site = Path.cwd(), Path(tmp) / "site"
                original, altered = Path(tmp) / "original.tar", Path(tmp) / "altered.tar"
                build(root, site)
                package(root, site, original)
                with tarfile.open(original) as source, tarfile.open(altered, "w") as target:
                    for member in source:
                        if case == "missing-directory" and member.name == "./assets": continue
                        data = source.extractfile(member).read() if member.isfile() else None
                        if case == "changed-content" and member.name == "./index.html":
                            data = b"changed"
                            member.size = len(data)
                        target.addfile(member, io.BytesIO(data) if data is not None else None)
                with self.assertRaises(ValueError): verify_archive(root, altered)

    def test_missing_security_extra_file_changed_bytes_and_symlinks_are_refused(self):
        for case in ("missing", "extra", "changed", "symlink"):
            with self.subTest(case=case), tempfile.TemporaryDirectory(prefix="pages-package-") as tmp:
                root, site = Path.cwd(), Path(tmp) / "site"
                build(root, site)
                security = site / ".well-known/security.txt"
                if case == "missing": security.unlink()
                if case == "extra": (site / "report.txt").write_text("fixture")
                if case == "changed": security.write_text("fixture")
                if case == "symlink":
                    security.unlink()
                    security.symlink_to(root / ".well-known/security.txt")
                with self.assertRaises(ValueError): package(root, site, Path(tmp) / "artifact.tar")

    def test_archive_refuses_missing_dot_paths_duplicate_extra_and_link_members(self):
        for case in ("missing", "duplicate", "extra", "link"):
            with self.subTest(case=case), tempfile.TemporaryDirectory(prefix="pages-package-") as tmp:
                archive = Path(tmp) / "artifact.tar"
                with tarfile.open(archive, "w") as tar:
                    member = tarfile.TarInfo(".nojekyll")
                    tar.addfile(member, io.BytesIO(b""))
                    if case != "missing":
                        other = tarfile.TarInfo(".nojekyll" if case == "duplicate" else "fixture.txt")
                        if case == "link": other.type = tarfile.SYMTYPE; other.linkname = "index.html"
                        tar.addfile(other)
                with self.assertRaises(ValueError): verify_archive(Path.cwd(), archive)


if __name__ == "__main__": unittest.main()
