import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from build_site import consumer_paths
from check_live_site import BASE_URL, REPOSITORY, NEGATIVE_PATHS, check_identity, check_public, main
from package_site import package


class PublicAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path.cwd()
        self.paths = consumer_paths(self.root)

    def response(self, path):
        if path in NEGATIVE_PATHS:
            return {"status": 404, "sha256": "not-found", "headers": {}}
        return {"status": 200, "sha256": hashlib.sha256((self.root / path).read_bytes()).hexdigest(),
                "headers": {"content-type": "text/plain; charset=utf-8"}}

    def test_all_declared_files_including_markers_and_exact_16_negative_paths_are_checked(self):
        seen = []
        def fetch(path):
            seen.append(path)
            return self.response(path)
        result = check_public(self.root, self.paths, fetch)
        self.assertTrue(result["passed"])
        self.assertEqual(result["positive_count"], len(self.paths))
        self.assertEqual(result["negative_count"], 16)
        self.assertEqual(set(seen), self.paths | set(NEGATIVE_PATHS))
        self.assertEqual(len(seen), len(self.paths) + 16)

    def test_legacy_bytes_fallback_redirect_missing_positive_and_bad_mime_fail(self):
        cases = (("README.md", {"status": 200}),
                 ("scripts/check_library.py", {"status": 200, "sha256": "html-fallback"}),
                 ("index.html", {"status": 302}),
                 ("index.html", {"status": 404}),
                 ("index.html", {"sha256": "changed"}),
                 (".well-known/security.txt", {"headers": {"content-type": "text/html"}}),
                 ("CNAME", {"status": None}),
                 (".nojekyll", {"status": 404}))
        for path, change in cases:
            with self.subTest(path=path, change=change):
                def fetch(p):
                    row = self.response(p)
                    if p == path: row.update(change)
                    return row
                result = check_public(self.root, self.paths, fetch)
                self.assertFalse(result["passed"])
                self.assertEqual([r["path"] for r in result["responses"] if not r["passed"]], [path])

    def test_identifiers_are_bound_to_completed_manual_main_run(self):
        run = dict(id=1, head_sha="a" * 40, event="workflow_dispatch", path=".github/workflows/pages.yml",
                   head_branch="main", status="completed", conclusion="success")
        artifact = dict(id=2, name="github-pages", expired=False, workflow_run=dict(id=1, head_sha="a" * 40))
        deployment = dict(sha="a" * 40, ref="main", environment="github-pages")
        statuses = [dict(state="success", environment_url=BASE_URL + "/", log_url="https://github.com/" + REPOSITORY + "/actions/runs/1/job/3")]
        records = [run, artifact, deployment, statuses, dict(status="succeed")]
        self.assertEqual(check_identity(*records, 1, 2), "a" * 40)
        for index, key, value in ((0, "head_branch", "topic"), (0, "event", "push"),
                                  (0, "conclusion", "failure"), (1, "id", 3),
                                  (1, "expired", True), (2, "sha", "b" * 40), (4, "status", "pending")):
            with self.subTest(index=index, key=key):
                changed = copy.deepcopy(records)
                changed[index][key] = value
                with self.assertRaises(ValueError): check_identity(*changed, 1, 2)
        changed = copy.deepcopy(records)
        changed[1]["workflow_run"]["id"] = 9
        with self.assertRaises(ValueError): check_identity(*changed, 1, 2)

    def test_cli_accepts_manifest_sized_archive_and_rejects_corruption(self):
        sha = "a" * 40
        run = dict(id=1, head_sha=sha, event="workflow_dispatch", path=".github/workflows/pages.yml",
                   head_branch="main", status="completed", conclusion="success")
        artifact = dict(id=2, name="github-pages", expired=False, workflow_run=dict(id=1, head_sha=sha))
        deployment = dict(sha=sha, ref="main", environment="github-pages")
        statuses = [dict(state="success", environment_url=BASE_URL + "/",
                         log_url="https://github.com/" + REPOSITORY + "/actions/runs/1/job/3")]
        with tempfile.TemporaryDirectory() as tmp:
            root, site = Path(tmp) / "root", Path(tmp) / "site"
            root.mkdir(); site.mkdir()
            for path in ("index.html", "reference/index.html"):
                for parent in (root, site):
                    (parent / path).parent.mkdir(parents=True, exist_ok=True)
                    (parent / path).write_text("<p>Reader page</p>")
            (root / "MANIFEST.md").write_text(
                "## Consumer artifact\n- `index.html`\n- `reference/index.html`\n"
                "## Repository-only files\n- `MANIFEST.md`\n")
            archive = Path(tmp) / "artifact.tar"
            package(root, site, archive)
            for valid in (True, False):
                with self.subTest(valid=valid):
                    stream = io.BytesIO()
                    with zipfile.ZipFile(stream, "w") as bundle:
                        bundle.writestr("artifact.tar", archive.read_bytes() if valid else b"not a tar archive")
                    output = Path(tmp) / ("valid.json" if valid else "invalid.json")
                    records = [run, artifact, deployment, statuses, dict(status="succeed"), stream.getvalue()]
                    def fetch(path, nonce):
                        if path in NEGATIVE_PATHS:
                            return dict(status=404, sha256="absent", headers={})
                        return dict(status=200, sha256=hashlib.sha256((root / path).read_bytes()).hexdigest(), headers={})
                    argv = ["check_live_site", "--run-id", "1", "--artifact-id", "2",
                            "--environment-deployment-id", "3", "--pages-deployment-id", sha,
                            "--output", str(output)]
                    with patch("sys.argv", argv), patch("check_live_site.Path.cwd", return_value=root), \
                         patch("check_live_site.api", side_effect=records), \
                         patch("check_live_site.subprocess.check_output", side_effect=[sha + "\n", b""]), \
                         patch("check_live_site.fetch", side_effect=fetch):
                        self.assertEqual(main(), 0 if valid else 1)
                    receipt = json.loads(output.read_text())
                    self.assertEqual(receipt["passed"], valid)
                    if valid:
                        self.assertEqual(receipt["archive_files_verified"], 2)
                        self.assertEqual(receipt["positive_count"], 2)
                        self.assertEqual(receipt["negative_count"], 16)
                    else:
                        self.assertIn("error", receipt)
        changed = copy.deepcopy(records)
        changed[3][0]["log_url"] = "https://github.com/x/y/actions/runs/9"
        with self.assertRaises(ValueError): check_identity(*changed, 1, 2)


if __name__ == "__main__": unittest.main()
