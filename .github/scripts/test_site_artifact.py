from pathlib import Path
import tempfile
import unittest
from build_site import build, consumer_paths


class SiteArtifactTests(unittest.TestCase):
    def test_real_site_has_only_consumer_paths_and_preserves_bytes(self):
        root = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="site-artifact-") as tmp:
            output = Path(tmp) / "site"
            paths = build(root, output)
            for path in paths:
                self.assertEqual((root / path).read_bytes(), (output / path).read_bytes(), path)
            self.assertIn(".well-known/security.txt", paths)
            self.assertIn("assets/fonts/ibm-plex/OFL.txt", paths)
            self.assertIn("robots.txt", paths)
            self.assertIn("sitemap.xml", paths)
            self.assertIn("llms.txt", paths)
            for path in paths:
                self.assertFalse(path.startswith(("scripts/", ".github/", "assets/inc/")), path)
                self.assertFalse(path.endswith((".py", ".woff2")), path)
            self.assertNotIn("README.md", paths)
            self.assertNotIn("MANIFEST.md", paths)
            self.assertNotIn("library/README.md", paths)
            self.assertNotIn("assets/img/studio-preview.png", paths)

    def fixture(self, root):
        (root / "index.html").write_text('<link rel="stylesheet" href="style.css">')
        (root / "style.css").write_text("body {}")
        (root / "MANIFEST.md").write_text("## Consumer artifact\n- `index.html`\n- `style.css`\n## Repository-only files\n- `MANIFEST.md`\n")

    def test_extra_source_tests_reports_and_directory_siblings_do_not_ship(self):
        with tempfile.TemporaryDirectory(prefix="site-artifact-") as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            self.fixture(root)
            for path in ("scripts/tool.py", ".github/workflows/test.yml", "report.txt", "tests/fixture.txt", "assets-extra/fixture.txt", ".well-known/fixture.txt"):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture")
            output = Path(tmp) / "site"
            self.assertEqual(build(root, output), {"index.html", "style.css"})

    def test_missing_dependency_missing_source_and_symlink_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="site-artifact-") as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            self.fixture(root)
            (root / "style.css").unlink()
            with self.assertRaises(ValueError):
                build(root, Path(tmp) / "missing-source")
            (root / "style.css").write_text('body { background: url("missing.png"); }')
            with self.assertRaisesRegex(ValueError, "Missing local reference"):
                build(root, Path(tmp) / "missing-link")
            (root / "style.css").unlink()
            (root / "outside.css").write_text("fixture")
            (root / "style.css").symlink_to(root / "outside.css")
            with self.assertRaisesRegex(ValueError, "Invalid consumer path"):
                build(root, Path(tmp) / "symlink")

    def test_ambiguous_consumer_section_and_existing_output_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="site-artifact-") as tmp:
            root = Path(tmp)
            self.fixture(root)
            with self.assertRaisesRegex(ValueError, "already exists"):
                build(root, root)
            (root / "MANIFEST.md").write_text("## Consumer artifact\n- `index.html`\n")
            with self.assertRaises(ValueError):
                consumer_paths(root)


if __name__ == "__main__":
    unittest.main()
