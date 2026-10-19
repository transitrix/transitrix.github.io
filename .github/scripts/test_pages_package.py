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
                self.assertTrue(all(member.isfile() for member in tar))

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
