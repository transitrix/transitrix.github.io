#!/usr/bin/env python3
"""Guard the library's shape and no-gate contract.

Checked against library/ (see library/README.md for the contract in prose): every
item directory carries <slug>.source.html and <slug>.pdf and no other file named
.pdf, the source's own `@page { size: <w>mm <h>mm }` rule matches the committed
PDF's MediaBox, the PDF is exactly one page, the source's `<title>` leads with the
item's own printed name (its `<h1>`), no item page contains a form/input/submit-
button/signup-script gate, and library/SHA256SUMS carries a matching pair of
hashes - source and PDF - for every item, byte-for-byte.

Usage: python3 scripts/check_library.py
Runs a self-test against throwaway fixtures in a temp directory before checking the
real tree - see .github/workflows/library.yml for the same shape.

Rendering happens only in scripts/render_library_item.py, on an agent's own host;
this check never launches a browser and never re-renders to verify - see
library/README.md for why a byte-diff re-render check is not attempted.
"""
import hashlib
import os
import re
import shutil
import sys
import tempfile

LIBRARY_DIR = "library"
CHECKSUMS_FILE = "SHA256SUMS"
NON_ITEM_ENTRIES = {"README.md", CHECKSUMS_FILE}
GEOMETRY_TOLERANCE_PT = 0.5

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


def find_slug_dirs(library_root):
    if not os.path.isdir(library_root):
        return []
    slugs = []
    for name in sorted(os.listdir(library_root)):
        if name in NON_ITEM_ENTRIES or name.startswith("."):
            continue
        if os.path.isdir(os.path.join(library_root, name)):
            slugs.append(name)
    return slugs


def source_path_for(library_root, slug):
    return os.path.join(library_root, slug, f"{slug}.source.html")


def pdf_path_for(library_root, slug):
    return os.path.join(library_root, slug, f"{slug}.pdf")


def check_shape(library_root, slug):
    errors = []
    slug_dir = os.path.join(library_root, slug)

    if not os.path.isfile(source_path_for(library_root, slug)):
        errors.append(f"{slug_dir}: missing {slug}.source.html")

    expected_pdf = f"{slug}.pdf"
    pdfs = [f for f in os.listdir(slug_dir) if f.lower().endswith(".pdf")]
    if expected_pdf not in pdfs:
        errors.append(f"{slug_dir}: missing {expected_pdf}")
    for f in pdfs:
        if f != expected_pdf:
            errors.append(f"{slug_dir}: PDF named {f!r}, expected only {expected_pdf!r}")
    return errors


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def check_gate(library_root, slug):
    errors = []
    source_path = source_path_for(library_root, slug)
    if not os.path.isfile(source_path):
        return errors
    html = _read(source_path)
    for pattern, label in GATE_PATTERNS:
        if pattern.search(html):
            errors.append(f"{source_path}: contains {label} - no gate is allowed on a library page")
    return errors


def check_title(library_root, slug):
    """The source's <title> must lead with the item's own printed name - the same
    convention library/README.md states for the served page, applied here to the
    source it will eventually be built from. The printed name is read from the
    source's own <h1>, so there is nothing outside the file to keep in sync."""
    source_path = source_path_for(library_root, slug)
    if not os.path.isfile(source_path):
        return []
    html = _read(source_path)

    title_m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if not title_m:
        return [f"{source_path}: no <title> element"]
    if not h1_m:
        return [f"{source_path}: no <h1> to read the item's printed name from"]

    title_text = re.sub(r"\s+", " ", title_m.group(1)).strip()
    h1_text = re.sub(r"<[^>]+>", "", h1_m.group(1))
    h1_text = re.sub(r"\s+", " ", h1_text).strip()

    if not h1_text.startswith(title_text):
        return [
            f"{source_path}: <title> {title_text!r} does not lead the printed name "
            f"{h1_text!r} (<h1>)"
        ]
    return []


def page_size_mm(source_path):
    html = _read(source_path)
    m = re.search(r"@page\s*\{[^}]*size:\s*([\d.]+)mm\s+([\d.]+)mm", html)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))


def mm_to_pt(mm):
    return mm * 72.0 / 25.4


def read_mediabox_and_page_count(pdf_path):
    with open(pdf_path, "rb") as f:
        data = f.read()
    boxes = re.findall(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]", data)
    if not boxes:
        return None
    page_count = len(re.findall(rb"/Type\s*/Page[^s]", data))
    w = float(boxes[0][2]) - float(boxes[0][0])
    h = float(boxes[0][3]) - float(boxes[0][1])
    return w, h, page_count


def check_geometry(library_root, slug):
    """Statically compares the source's own @page rule against the committed PDF's
    MediaBox and page count - never by re-rendering (see module docstring)."""
    source_path = source_path_for(library_root, slug)
    pdf_path = pdf_path_for(library_root, slug)
    if not os.path.isfile(source_path) or not os.path.isfile(pdf_path):
        return []

    want_mm = page_size_mm(source_path)
    if want_mm is None:
        return [f"{source_path}: no `@page {{ size: <w>mm <h>mm }}` rule"]
    want_w_pt, want_h_pt = mm_to_pt(want_mm[0]), mm_to_pt(want_mm[1])

    got = read_mediabox_and_page_count(pdf_path)
    if got is None:
        return [f"{pdf_path}: no /MediaBox found"]
    got_w_pt, got_h_pt, page_count = got

    errors = []
    if page_count != 1:
        errors.append(f"{pdf_path}: expected exactly 1 page, found {page_count}")
    if abs(got_w_pt - want_w_pt) > GEOMETRY_TOLERANCE_PT or abs(got_h_pt - want_h_pt) > GEOMETRY_TOLERANCE_PT:
        errors.append(
            f"{pdf_path}: MediaBox {got_w_pt:.2f}x{got_h_pt:.2f}pt does not match "
            f"{source_path}'s @page size {want_w_pt:.2f}x{want_h_pt:.2f}pt "
            f"(tolerance {GEOMETRY_TOLERANCE_PT}pt)"
        )
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


def check_checksums(library_root, slugs):
    """Every item carries a *pair* of entries - source and PDF - each verified
    against the committed file it names. A source edited without re-rendering is
    caught here: its committed bytes no longer match the hash recorded for it,
    the same way a tampered PDF already was. See library/README.md for the failure
    mode this exists to catch and the one it deliberately does not attempt."""
    checksums_path = os.path.join(library_root, CHECKSUMS_FILE)
    try:
        entries = parse_checksums(checksums_path)
    except ValueError as e:
        return [str(e)]
    if entries is None:
        return [f"{checksums_path}: missing"]

    errors = []
    committed = {}
    for slug in slugs:
        for rel, abs_path in (
            (f"{slug}/{slug}.source.html", source_path_for(library_root, slug)),
            (f"{slug}/{slug}.pdf", pdf_path_for(library_root, slug)),
        ):
            if os.path.isfile(abs_path):
                committed[rel] = abs_path

    for rel, abs_path in committed.items():
        if rel not in entries:
            errors.append(f"{checksums_path}: no entry for {rel}")
            continue
        actual = sha256_of(abs_path)
        if actual != entries[rel]:
            errors.append(
                f"{checksums_path}: checksum for {rel} does not match the committed file "
                f"(expected {entries[rel]}, got {actual})"
            )

    for rel in entries:
        if rel not in committed:
            errors.append(f"{checksums_path}: entry for {rel} but no such file exists")

    return errors


def run_checks(root):
    library_root = os.path.join(root, LIBRARY_DIR)
    slugs = find_slug_dirs(library_root)
    errors = []
    for slug in slugs:
        errors.extend(check_shape(library_root, slug))
        errors.extend(check_gate(library_root, slug))
        errors.extend(check_title(library_root, slug))
        errors.extend(check_geometry(library_root, slug))
    errors.extend(check_checksums(library_root, slugs))
    return errors, slugs


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


PAGE_W_MM, PAGE_H_MM = 100.0, 50.0
PAGE_W_PT, PAGE_H_PT = mm_to_pt(PAGE_W_MM), mm_to_pt(PAGE_H_MM)


def _fixture_source(title="Widgets", h1="Widgets — the complete field guide", extra_head="", extra_body=""):
    return (
        "<!DOCTYPE html><html><head>"
        f"<title>{title}</title>"
        f"<style>@page {{ size: {PAGE_W_MM:g}mm {PAGE_H_MM:g}mm; margin: 0; }}</style>"
        f"{extra_head}"
        f"</head><body><h1>{h1}</h1>{extra_body}</body></html>"
    )


def _fixture_pdf(w_pt=PAGE_W_PT, h_pt=PAGE_H_PT, page_count=1):
    pages = "".join(f"<< /Type /Page /MediaBox [0 0 {w_pt:.2f} {h_pt:.2f}] >>\n" for _ in range(page_count))
    return f"%PDF-1.4\n{pages}%%EOF".encode("ascii")


def _sha256sums_lines(root_for_hash, slug):
    source_path = source_path_for(os.path.join(root_for_hash, LIBRARY_DIR), slug)
    pdf_path = pdf_path_for(os.path.join(root_for_hash, LIBRARY_DIR), slug)
    return (
        f"{sha256_of(source_path)}  {slug}/{slug}.source.html\n"
        f"{sha256_of(pdf_path)}  {slug}/{slug}.pdf\n"
    )


def _fresh_item(tmp, slug="widgets", source_html=None, pdf_bytes=None):
    """A minimal, contract-clean item: <slug>.source.html, <slug>.pdf, and a
    matching pair of SHA256SUMS entries. Callers mutate one thing at a time to
    demonstrate a failure."""
    _write(source_path_for(os.path.join(tmp, LIBRARY_DIR), slug), source_html or _fixture_source())
    with open(pdf_path_for(os.path.join(tmp, LIBRARY_DIR), slug), "wb") as f:
        f.write(pdf_bytes if pdf_bytes is not None else _fixture_pdf())
    _write(os.path.join(tmp, LIBRARY_DIR, CHECKSUMS_FILE), _sha256sums_lines(tmp, slug))
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

    # A clean item passes outright.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp)
        errors, slugs = run_checks(tmp)
        _expect(errors == [], "a contract-clean item passes with zero errors", "a clean item was flagged", failures)
    finally:
        shutil.rmtree(tmp)

    # Zero items present passes vacuously, provided SHA256SUMS exists (empty).
    tmp = tempfile.mkdtemp()
    try:
        _write(os.path.join(tmp, LIBRARY_DIR, CHECKSUMS_FILE), "")
        errors, slugs = run_checks(tmp)
        _expect(errors == [] and slugs == [], "zero items present passes vacuously", "an empty library was flagged", failures)
    finally:
        shutil.rmtree(tmp)

    # Missing source.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp)
        os.remove(source_path_for(os.path.join(tmp, LIBRARY_DIR), slug))
        errors, _ = run_checks(tmp)
        _expect(
            any("missing widgets.source.html" in e for e in errors),
            "an item directory missing <slug>.source.html is caught",
            "a missing source was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Missing PDF.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp)
        os.remove(pdf_path_for(os.path.join(tmp, LIBRARY_DIR), slug))
        errors, _ = run_checks(tmp)
        _expect(
            any(f"missing {slug}.pdf" in e for e in errors),
            "an item directory missing <slug>.pdf is caught",
            "a missing PDF was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # PDF named wrong (not <slug>.pdf).
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp)
        os.rename(
            pdf_path_for(os.path.join(tmp, LIBRARY_DIR), slug),
            os.path.join(tmp, LIBRARY_DIR, slug, "final-v2.pdf"),
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
        slug = _fresh_item(tmp, source_html=_fixture_source(extra_body="<form></form>"))
        errors, _ = run_checks(tmp)
        _expect(
            any("<form>" in e for e in errors),
            "a source with a <form> gate is caught",
            "a <form> gate was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: <input>.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp, source_html=_fixture_source(extra_body='<input type="email">'))
        errors, _ = run_checks(tmp)
        _expect(
            any("<input>" in e for e in errors),
            "a source with a bare <input> gate is caught",
            "an <input> gate was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: <button type="submit">.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp, source_html=_fixture_source(extra_body='<button type="submit">Get it</button>'))
        errors, _ = run_checks(tmp)
        _expect(
            any('type="submit"' in e for e in errors),
            'a source with a <button type="submit"> gate is caught',
            "a submit-button gate was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: mail-capture/signup script.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(
            tmp,
            source_html=_fixture_source(extra_head='<script src="https://embed.mailchimp.com/embed.js"></script>'),
        )
        errors, _ = run_checks(tmp)
        _expect(
            any("mail-capture/signup script" in e for e in errors),
            "a source embedding a signup-form script is caught",
            "a signup-script gate was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Gate: interstitial marker.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp, source_html=_fixture_source(extra_body='<div class="signup-modal">Before you download...</div>'))
        errors, _ = run_checks(tmp)
        _expect(
            any("interstitial/gate marker" in e for e in errors),
            "a source carrying an interstitial/gate marker is caught",
            "an interstitial marker was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Title does not lead the printed name.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp, source_html=_fixture_source(title="Gadgets"))
        errors, _ = run_checks(tmp)
        _expect(
            any("does not lead the printed name" in e for e in errors),
            "a <title> that does not lead the <h1> printed name is caught",
            "a mismatched title was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Page geometry mismatch.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp, pdf_bytes=_fixture_pdf(w_pt=PAGE_W_PT + 5))
        errors, _ = run_checks(tmp)
        _expect(
            any("does not match" in e and "MediaBox" in e for e in errors),
            "a PDF whose MediaBox disagrees with the source's @page size is caught",
            "a geometry mismatch was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # Page count != 1.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp, pdf_bytes=_fixture_pdf(page_count=2))
        errors, _ = run_checks(tmp)
        _expect(
            any("expected exactly 1 page" in e for e in errors),
            "a PDF with more than one page is caught",
            "a page-count mismatch was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # SHA256SUMS mismatch - a source edited without re-rendering (its checksum
    # entry left stale) is exactly this case.
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp)
        with open(source_path_for(os.path.join(tmp, LIBRARY_DIR), slug), "a", encoding="utf-8") as f:
            f.write("<!-- edited after the checksum was recorded, never re-rendered -->")
        errors, _ = run_checks(tmp)
        _expect(
            any(f"checksum for {slug}/{slug}.source.html does not match" in e for e in errors),
            "a source edited without re-rendering (stale checksum) is caught",
            "an edited-without-re-rendering source was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # SHA256SUMS mismatch on the PDF side (tampering after the fact).
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp)
        with open(pdf_path_for(os.path.join(tmp, LIBRARY_DIR), slug), "ab") as f:
            f.write(b"tampered after the checksum was recorded")
        errors, _ = run_checks(tmp)
        _expect(
            any(f"checksum for {slug}/{slug}.pdf does not match" in e for e in errors),
            "a PDF that no longer matches SHA256SUMS is caught",
            "a checksum mismatch was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    # SHA256SUMS stale entry (files removed, entries left behind).
    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp)
        checksums_path = os.path.join(tmp, LIBRARY_DIR, CHECKSUMS_FILE)
        with open(checksums_path, "a", encoding="utf-8") as f:
            f.write("0" * 64 + "  ghost/ghost.pdf\n")
        errors, _ = run_checks(tmp)
        _expect(
            any("entry for ghost/ghost.pdf but no such file exists" in e for e in errors),
            "a SHA256SUMS entry with no matching file is caught",
            "a stale checksum entry was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    if failures:
        print(f"::error::check_library self-test failed - {len(failures)} check(s) did not behave as expected, not trusting its verdict on the real tree")
        return 1
    print("self-test: all failure modes are caught, and a clean tree passes.")
    return 0


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    selftest_status = _selftest()
    if selftest_status != 0:
        return selftest_status

    print("== Checking library/ against the committed tree ==")
    errors, slugs = run_checks(root)
    for e in errors:
        print(f"::error::{e}")
    if errors:
        print(f"check_library: {len(errors)} problem(s), see above")
        return 1
    note = " (zero items present)" if not slugs else f" ({len(slugs)} item(s))"
    print(f"check_library: library/ contract holds{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
