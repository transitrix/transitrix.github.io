import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from check_publish_manifest import parse_manifest

SCRIPT = Path(__file__).with_name("check_publish_manifest.py").resolve()


class ManifestTests(unittest.TestCase):
    def test_current_tree(self):
        allowed = parse_manifest(Path("MANIFEST.md").read_text())
        tracked = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
        self.assertEqual([p for p in tracked if p and p not in allowed], [])

    def test_exact_paths_and_invalid_declarations(self):
        allowed = parse_manifest("- `allowed/file.txt`\n")
        self.assertIn("allowed/file.txt", allowed)
        for path in ("allowed/other.txt", "allowed-extra/file.txt", "allowed/file.txt/child"):
            self.assertNotIn(path, allowed)
        for path in ("allowed/**", "allowed/", "*", "../file", "/file", "a/./b", "a//b", "a\\b", "a b"):
            with self.assertRaises(ValueError):
                parse_manifest(f"- `{path}`\n")
        for text in ("", "- `README.md`\n- `README.md`\n"):
            with self.assertRaises(ValueError):
                parse_manifest(text)

    def test_cli_full_tree_without_diff_context(self):
        with tempfile.TemporaryDirectory(prefix="manifest-case-") as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)
            def put(path, text="fixture"):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
            def run(**env):
                return subprocess.run([sys.executable, str(SCRIPT)], cwd=root, text=True,
                                      capture_output=True, env={**os.environ, "BASE_SHA": "", "HEAD_SHA": "", **env})
            git("init", "-q")
            git("config", "user.name", "fixture")
            git("config", "user.email", "fixture@example.invalid")
            put("allowed/file.txt")
            put("MANIFEST.md", "- `allowed/file.txt`\n- `MANIFEST.md`\n")
            git("add", ".")
            git("commit", "-qm", "Fixture baseline")
            self.assertEqual(run().returncode, 0)
            put("allowed/file.txt", "changed")
            git("add", ".")
            self.assertEqual(run().returncode, 0)
            for path in ("new.txt", "allowed/other.txt", "allowed-extra/file.txt", "scripts/fixture.txt", ".well-known/fixture.txt"):
                put(path)
                git("add", path)
                denied = run()
                self.assertEqual(denied.returncode, 1)
                self.assertIn(path, denied.stderr)
                git("rm", "-qf", path)
            put("existing.txt")
            git("add", ".")
            git("commit", "-qm", "Fixture existing undeclared")
            put("existing.txt", "changed")
            git("add", ".")
            self.assertEqual(run().returncode, 1)
            self.assertIn("existing.txt", run().stderr)
            self.assertEqual(run(BASE_SHA="invalid", HEAD_SHA="invalid").returncode, 1)
            (root / "MANIFEST.md").unlink()
            self.assertEqual(run().returncode, 1)


if __name__ == "__main__":
    unittest.main()
