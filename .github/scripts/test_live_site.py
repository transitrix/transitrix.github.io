import copy
import hashlib
from pathlib import Path
import unittest
from build_site import consumer_paths
from check_live_site import BASE_URL, REPOSITORY, NEGATIVE_PATHS, check_identity, check_public


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
        changed = copy.deepcopy(records)
        changed[3][0]["log_url"] = "https://github.com/x/y/actions/runs/9"
        with self.assertRaises(ValueError): check_identity(*changed, 1, 2)


if __name__ == "__main__": unittest.main()
