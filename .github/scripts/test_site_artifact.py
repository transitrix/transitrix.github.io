from pathlib import Path
from html.parser import HTMLParser
import tempfile
import unittest
from urllib.parse import urljoin
from build_site import build, consumer_paths


class Navigation(HTMLParser):
    def __init__(self):
        super().__init__()
        self.navs = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav":
            self.current = {"class": attrs.get("class"), "label": attrs.get("aria-label"), "links": []}
            self.navs.append(self.current)
        elif tag == "a" and self.current is not None:
            self.current["links"].append({**attrs, "text": ""})

    def handle_data(self, text):
        if self.current is not None and self.current["links"]:
            self.current["links"][-1]["text"] += text

    def handle_endtag(self, tag):
        if tag == "nav":
            self.current = None


class SiteArtifactTests(unittest.TestCase):
    def test_reader_pages_expose_the_primary_destinations_in_initial_html(self):
        root = Path.cwd()
        for path in sorted(consumer_paths(root)):
            if not path.endswith("index.html") or path == "marketplace-status/index.html":
                continue
            html = (root / path).read_text()
            if '<header class="site-header">' not in html:
                continue
            with self.subTest(page=path):
                parser = Navigation()
                parser.feed(html)
                menus = [nav for nav in parser.navs if nav["class"] == "site-nav"]
                self.assertEqual(len(menus), 1)
                german = path.startswith("de/")
                expected = [
                    ("/learn/", "Lernen (EN)" if german else "Learn"),
                    ("/de/dsl-examples/" if german else "/dsl-examples/", "Beispiele" if german else "Examples"),
                    ("https://github.com/transitrix/methodology", "Methodik (EN)" if german else "Methodology"),
                    ("/library/", "Bibliothek (EN)" if german else "Library"),
                    ("/de/install/" if german else "/install/", "Installieren & starten" if german else "Install & start"),
                ]
                self.assertEqual(menus[0]["label"], "Hauptnavigation" if german else "Primary")
                self.assertEqual([(a["href"], a["text"].strip()) for a in menus[0]["links"]], expected)
                methodology = menus[0]["links"][2]
                self.assertEqual(methodology.get("target"), "_blank")
                self.assertEqual(set(methodology.get("rel", "").split()), {"noopener", "noreferrer"})
                for href, _ in expected:
                    if href.startswith("/"):
                        self.assertTrue((root / href.lstrip("/") / "index.html").is_file())

    def test_learning_path_can_be_followed_forward_and_backward(self):
        steps = ["what-is-transitrix", "vs-drawing-tools", "enterprise-as-text", "do-i-need-dsm",
                 "which-editor", "install", "strategy-and-behaviour", "is-it-open-source"]
        for i, slug in enumerate(steps):
            with self.subTest(page=slug):
                parser = Navigation()
                parser.feed((Path(slug) / "index.html").read_text())
                navs = [nav for nav in parser.navs if nav["label"] == "Learning path navigation"]
                self.assertEqual(len(navs), 1)
                expected = ["/" + (steps[i - 1] if i else "learn") + "/",
                            "/" + (steps[i + 1] if i + 1 < len(steps) else "dsl-examples") + "/"]
                self.assertEqual([urljoin("/" + slug + "/", a["href"]) for a in navs[0]["links"]], expected)

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
