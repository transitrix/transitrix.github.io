#!/usr/bin/env python3
"""Read-only acceptance of a completed Pages run and its exact public files."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from http.client import HTTPException
import io
import json
from pathlib import Path
import subprocess
import tempfile
import tarfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid
import zipfile

from package_site import verify_archive

REPOSITORY = "transitrix/transitrix.github.io"
BASE_URL = "https://transitrix.com"
NEGATIVE_PATHS = (
    ".gitignore", "MANIFEST.md", "README.md",
    "assets/fonts/ibm-plex/IBMPlexMono-Medium.woff2",
    "assets/fonts/ibm-plex/IBMPlexMono-Regular.woff2",
    "assets/fonts/ibm-plex/IBMPlexSans-Bold.woff2",
    "assets/fonts/ibm-plex/IBMPlexSans-Medium.woff2",
    "assets/fonts/ibm-plex/IBMPlexSans-Regular.woff2",
    "assets/fonts/ibm-plex/IBMPlexSans-SemiBold.woff2",
    "assets/img/studio-preview.png", "assets/inc/favicon-links.html",
    "assets/inc/og-meta.html", "library/README.md",
    "scripts/check_explainers.py", "scripts/check_library.py", "scripts/generate_sitemap.py",
)
SAFE_HEADERS = ("content-type", "cache-control", "age", "etag", "last-modified",
                "date", "server", "via", "x-cache", "x-proxy-cache", "x-served-by",
                "x-github-request-id", "x-fastly-request-id", "x-github-edge-region")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(path, nonce):
    url = BASE_URL + "/" + quote(path, safe="/") + "?acceptance=" + nonce
    request = Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "site-public-acceptance"})
    try:
        response = build_opener(NoRedirect).open(request, timeout=20)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError):
        return {"status": None, "sha256": None, "headers": {}, "error": "request-failed"}
    try:
        with response:
            data = response.read()
            return {"status": response.code, "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data), "headers": {key: response.headers[key] for key in SAFE_HEADERS
                                                    if key in response.headers}}
    except (HTTPException, OSError):
        return {"status": None, "sha256": None, "headers": {}, "error": "response-read-failed"}


def check_public(root, paths, fetcher):
    if set(paths) & set(NEGATIVE_PATHS):
        raise ValueError("Positive and negative declarations overlap")
    def check(item):
        path, positive = item
        row = {"path": path, "kind": "positive" if positive else "negative", **fetcher(path)}
        expected = hashlib.sha256((root / path).read_bytes()).hexdigest() if positive else None
        passed = row["status"] == (200 if positive else 404)
        if positive:
            row["expected_sha256"] = expected
            passed = passed and row["sha256"] == expected
        if path == ".well-known/security.txt":
            mime = row["headers"].get("content-type", "").split(";", 1)[0].strip().lower()
            passed = passed and mime == "text/plain"
        row["passed"] = passed
        return row
    items = [(p, True) for p in sorted(paths)] + [(p, False) for p in NEGATIVE_PATHS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, items))
    return {"passed": all(row["passed"] for row in rows), "positive_count": len(paths),
            "negative_count": len(NEGATIVE_PATHS), "responses": rows}


def check_identity(run, artifact, deployment, statuses, pages, run_id, artifact_id):
    sha = run["head_sha"]
    valid = (
        run["id"] == run_id and run["event"] == "workflow_dispatch"
        and run["path"] == ".github/workflows/pages.yml" and run["head_branch"] == "main"
        and run["status"] == "completed" and run["conclusion"] == "success"
        and artifact["id"] == artifact_id and artifact["name"] == "github-pages"
        and not artifact["expired"] and artifact["workflow_run"]["id"] == run_id
        and artifact["workflow_run"]["head_sha"] == sha
        and deployment["sha"] == sha and deployment["ref"] == "main"
        and deployment["environment"] == "github-pages"
        and any(s["state"] == "success" and s.get("environment_url", "").rstrip("/") == BASE_URL
                and s.get("log_url", "").startswith("https://github.com/" + REPOSITORY
                    + "/actions/runs/" + str(run_id) + "/") for s in statuses)
        and pages["status"] == "succeed"
    )
    if not valid:
        raise ValueError("Deployment identifiers do not describe a successful matching Pages run")
    return sha


def api(suffix, binary=False):
    result = subprocess.run(["gh", "api", "repos/" + REPOSITORY + "/" + suffix], capture_output=True)
    if result.returncode:
        raise ValueError("GitHub read failed: " + suffix)
    return result.stdout if binary else json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--environment-deployment-id", type=int, required=True)
    parser.add_argument("--pages-deployment-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output path must not exist")
    receipt = {"repository": REPOSITORY, "run_id": args.run_id, "artifact_id": args.artifact_id,
               "environment_deployment_id": args.environment_deployment_id,
               "pages_deployment_id": args.pages_deployment_id, "base_url": BASE_URL,
               "started_at": datetime.now(timezone.utc).isoformat(), "passed": False}
    try:
        # IDs come from the actual deployment log and environment record, not a latest-run guess.
        run = api(f"actions/runs/{args.run_id}")
        artifact = api(f"actions/artifacts/{args.artifact_id}")
        deployment = api(f"deployments/{args.environment_deployment_id}")
        statuses = api(f"deployments/{args.environment_deployment_id}/statuses")
        pages = api("pages/deployments/" + quote(args.pages_deployment_id, safe=""))
        receipt["sha"] = check_identity(run, artifact, deployment, statuses, pages, args.run_id, args.artifact_id)
        if args.pages_deployment_id != receipt["sha"]:
            raise ValueError("Pages deployment ID differs from the default SHA build version")
        root = Path.cwd()
        local_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        if local_sha != receipt["sha"] or subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"]):
            raise ValueError("Run from a clean checkout of the deployed SHA")
        zipped = api(f"actions/artifacts/{args.artifact_id}/zip", binary=True)
        with zipfile.ZipFile(io.BytesIO(zipped)) as bundle:
            if bundle.namelist() != ["artifact.tar"]:
                raise ValueError("Unexpected artifact container")
            data = bundle.read("artifact.tar")
        receipt["archive_sha256"] = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory(prefix="site-acceptance-") as tmp:
            archive = Path(tmp) / "artifact.tar"
            archive.write_bytes(data)
            paths = verify_archive(root, archive)
        receipt["archive_files_verified"] = len(paths)
        nonce = uuid.uuid4().hex
        receipt.update(check_public(root, paths, lambda path: fetch(path, nonce)))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile, tarfile.TarError) as error:
        receipt["error"] = str(error)
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(receipt, indent=2) + "\n")
    print("Public acceptance " + ("passed" if receipt["passed"] else "failed") + ": " + str(args.output))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
