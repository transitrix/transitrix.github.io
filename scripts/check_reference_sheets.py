#!/usr/bin/env python3
"""Guard the reference-sheet library's shape and no-gate contract.

Checked against reference-sheets/ (see reference-sheets/README.md for the contract
in prose): every sheet directory carries index.html and <slug>.pdf and nothing else
named .pdf, no sheet page contains a form/input/submit-button/signup-script gate,
and reference-sheets/SHA256SUMS matches the committed PDFs byte-for-byte.

Usage: python3 scripts/check_reference_sheets.py
Runs a self-test against throwaway fixtures in a temp directory before checking the
real tree - see .github/workflows/indexing-declarations.yml for the same shape.
"""
import hashlib
import os
import re
import shutil
import sys
import tempfile

REFERENCE_SHEETS_DIR = "reference-sheets"
CHECKSUMS_FILE = "SHA256SUMS"
NON_SHEET_ENTRIES = {"README.md", CHECKSUMS_FILE}

GATE_PATTERNS = [
    (re.compile(r"<form\b", re.IGNORECASE), "a <form> element"),
    (re.compile(r"<input\b", re.IGNORECASE), "an <input> element"),
    (re.compile(r'<button[^>]*type\s*=\s*["\']?submit', re.IGNORECASE), 'a <button type="submit">'),
    (
        re.compile(
            r"(mailchimp|convertkit|hubspot|getresponse|klaviyo|substack|beehiiv|typeform)",
            re.IGNORECASE,
        ),
        "a mail-capture/signup script",
    ),
    (
        re.compile(r"(interstitial|signup-modal|email-gate|paywall)", re.IGNORECASE),
        "an interstitial/gate marker",
    ),
]


def find_slug_dirs(sheets_root):
    if not os.path.isdir(sheets_root):
        return []
    slugs = []
    for name in sorted(os.listdir(sheets_root)):
        if name in NON_SHEET_ENTRIES or name.startswith("."):
            continue
        if os.path.isdir(os.path.join(sheets_root, name)):
            slugs.append(name)
    return slugs


def check_shape(sheets_root, slug):
    errors = []
    slug_dir = os.path.join(sheets_root, slug)
    index_path = os.path.join(slug_dir, "index.html")
    if not os.path.isfile(index_path):
        errors.append(f"{slug_dir}: missing index.html")

    expected_pdf = f"{slug}.pdf"
    pdfs = [f for f in os.listdir(slug_dir) if f.lower().endswith(".pdf")]
    if expected_pdf not in pdfs:
        errors.append(f"{slug_dir}: missing {expected_pdf}")
    for f in pdfs:
        if f != expected_pdf:
            errors.append(f"{slug_dir}: PDF named {f!r}, expected only {expected_pdf!r}")
    return errors


def check_gate(sheets_root, slug):
    errors = []
    index_path = os.path.join(sheets_root, slug, "index.html")
    if not os.path.isfile(index_path):
        return errors
    with open(index_path, encoding="utf-8") as f:
        html = f.read()
    for pattern, label in GATE_PATTERNS:
        if pattern.search(html):
            errors.append(f"{index_path}: contains {label} - no gate is allowed on a reference-sheet page")
    return errors


def parse_checksums(checksums_path):
    """Returns {relative_path: lowercase_hex_sha256}, or None if the file is missing."""
    if not os.path.isfile(checksums_path):
        return None
    entries = {}
    with open(checksums_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            m = re.match(r"^([0-9a-fA-F]{64})\s+(.+)$", line)
            if not m:
                raise ValueError(f"{checksums_path}:{lineno}: unparseable line {line!r}")
            entries[m.group(2).strip()] = m.group(1).lower()
    return entries


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def check_checksums(sheets_root, slugs):
    checksums_path = os.path.join(sheets_root, CHECKSUMS_FILE)
    try:
        entries = parse_checksums(checksums_path)
    except ValueError as e:
        return [str(e)]
    if entries is None:
        return [f"{checksums_path}: missing"]

    errors = []
    pdf_by_rel = {}
    for slug in slugs:
        rel = f"{slug}/{slug}.pdf"
        abs_path = os.path.join(sheets_root, slug, f"{slug}.pdf")
        if os.path.isfile(abs_path):
            pdf_by_rel[rel] = abs_path

    for rel, abs_path in pdf_by_rel.items():
        if rel not in entries:
            errors.append(f"{checksums_path}: no entry for {rel}")
            continue
        actual = sha256_of(abs_path)
        if actual != entries[rel]:
            errors.append(
                f"{checksums_path}: checksum for {rel} does not match the committed PDF "
                f"(expected {entries[rel]}, got {actual})"
            )

    for rel in entries:
        if rel not in pdf_by_rel:
            errors.append(f"{checksums_path}: entry for {rel} but no such PDF exists")

    return errors


def run_checks(root):
    sheets_root = os.path.join(root, REFERENCE_SHEETS_DIR)
    slugs = find_slug_dirs(sheets_root)
    errors = []
    for slug in slugs:
        errors.extend(check_shape(sheets_root, slug))
        errors.extend(check_gate(sheets_root, slug))
    errors.extend(check_checksums(sheets_root, slugs))
    return errors, slugs


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _sha256sums_line(root_for_hash, slug):
    pdf_path = os.path.join(root_for_hash, REFERENCE_SHEETS_DIR, slug, f"{slug}.pdf")
    return f"{sha256_of(pdf_path)}  {slug}/{slug}.pdf\n"


def _fresh_sheet(tmp, slug="widgets", pdf_bytes=b"%PDF-1.4 fixture\n"):
    """A minimal, contract-clean sheet: index.html, <slug>.pdf, and a matching
    SHA256SUMS entry. Callers mutate one thing at a time to demonstrate a failure."""
    _write(os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, "index.html"), "<html><body>content</body></html>")
    _write(os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, f"{slug}.pdf"))
    with open(os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, f"{slug}.pdf"), "wb") as f:
        f.write(pdf_bytes)
    _write(
        os.path.join(tmp, REFERENCE_SHEETS_DIR, CHECKSUMS_FILE),
        _sha256sums_line(tmp, slug),
    )
    return slug


def _expect(condition, ok_msg, fail_msg, failures):
    if condition:
        print(f"ok: {ok_msg}")
    else:
        print(f"::error::self-test regression - {fail_msg}")
        failures.append(fail_msg)


def _selftest():
    print("== Self-test: the checker itself must catch what it's meant to catch ==")
    failures = []

    # A clean sheet passes outright.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        errors, slugs = run_checks(tmp)
        _expect(errors == [], "a contract-clean sheet passes with zero errors", "a clean sheet was flagged", failures)
    finally:
        shutil.rmtree(tmp)

    # Zero sheets present passes vacuously, provided SHA256SUMS exists (empty).
    tmp = tempfile.mkdtemp()
    try:
        _write(os.path.join(tmp, REFERENCE_SHEETS_DIR, CHECKSUMS_FILE), "")
        errors, slugs = run_checks(tmp)
        _expect(errors == [] and slugs == [], "zero sheets present passes vacuously", "an empty library was flagged", failures)
    finally:
        shutil.rmtree(tmp)

    # Missing index.html.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        os.remove(os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, "index.html"))
        errors, _ = run_checks(tmp)
        _expect(
            any("missing index.html" in e for e in errors),
            "a sheet directory missing index.html is caught",
            "a missing index.html was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Missing PDF.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        os.remove(os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, f"{slug}.pdf"))
        errors, _ = run_checks(tmp)
        _expect(
            any(f"missing {slug}.pdf" in e for e in errors),
            "a sheet directory missing <slug>.pdf is caught",
            "a missing PDF was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # PDF named wrong (not <slug>.pdf).
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        os.rename(
            os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, f"{slug}.pdf"),
            os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, "final-v2.pdf"),
        )
        errors, _ = run_checks(tmp)
        _expect(
            any("PDF named 'final-v2.pdf'" in e for e in errors),
            "a PDF whose name is not <slug>.pdf is caught",
            "a misnamed PDF was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: <form>.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        _write(os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, "index.html"), '<html><body><form></form></body></html>')
        errors, _ = run_checks(tmp)
        _expect(
            any("<form>" in e for e in errors),
            "a page with a <form> gate is caught",
            "a <form> gate was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: <input>.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        _write(os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, "index.html"), '<html><body><input type="email"></body></html>')
        errors, _ = run_checks(tmp)
        _expect(
            any("<input>" in e for e in errors),
            "a page with a bare <input> gate is caught",
            "an <input> gate was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: <button type="submit">.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        _write(
            os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, "index.html"),
            '<html><body><button type="submit">Get it</button></body></html>',
        )
        errors, _ = run_checks(tmp)
        _expect(
            any('type="submit"' in e for e in errors),
            'a page with a <button type="submit"> gate is caught',
            "a submit-button gate was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: mail-capture/signup script.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        _write(
            os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, "index.html"),
            '<html><head><script src="https://embed.mailchimp.com/embed.js"></script></head><body>content</body></html>',
        )
        errors, _ = run_checks(tmp)
        _expect(
            any("mail-capture/signup script" in e for e in errors),
            "a page embedding a signup-form script is caught",
            "a signup-script gate was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: interstitial marker.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        _write(
            os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, "index.html"),
            '<html><body><div class="signup-modal">Before you download...</div></body></html>',
        )
        errors, _ = run_checks(tmp)
        _expect(
            any("interstitial/gate marker" in e for e in errors),
            "a page carrying an interstitial/gate marker is caught",
            "an interstitial marker was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # SHA256SUMS mismatch.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        with open(os.path.join(tmp, REFERENCE_SHEETS_DIR, slug, f"{slug}.pdf"), "ab") as f:
            f.write(b"tampered after the checksum was recorded")
        errors, _ = run_checks(tmp)
        _expect(
            any("does not match the committed PDF" in e for e in errors),
            "a PDF that no longer matches SHA256SUMS is caught",
            "a checksum mismatch was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # SHA256SUMS stale entry (PDF removed, entry left behind).
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_sheet(tmp)
        second = os.path.join(tmp, REFERENCE_SHEETS_DIR, CHECKSUMS_FILE)
        with open(second, "a", encoding="utf-8") as f:
            f.write("0" * 64 + "  ghost/ghost.pdf\n")
        errors, _ = run_checks(tmp)
        _expect(
            any("entry for ghost/ghost.pdf but no such PDF exists" in e for e in errors),
            "a SHA256SUMS entry with no matching PDF is caught",
            "a stale checksum entry was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    if failures:
        print(f"::error::check_reference_sheets self-test failed - {len(failures)} check(s) did not behave as expected, not trusting its verdict on the real tree")
        return 1
    print("self-test: all failure modes are caught, and a clean tree passes.")
    return 0


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    selftest_status = _selftest()
    if selftest_status != 0:
        return selftest_status

    print("== Checking reference-sheets/ against the committed tree ==")
    errors, slugs = run_checks(root)
    for e in errors:
        print(f"::error::{e}")
    if errors:
        print(f"check_reference_sheets: {len(errors)} problem(s), see above")
        return 1
    note = " (zero sheets present)" if not slugs else f" ({len(slugs)} sheet(s))"
    print(f"check_reference_sheets: reference-sheets/ contract holds{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
