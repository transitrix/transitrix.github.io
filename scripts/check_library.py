#!/usr/bin/env python3
"""Guard the library's published PDFs.

Checked against library/ (see library/README.md for the contract in prose): every
item directory carries <slug>.pdf and no other file named .pdf, the PDF is exactly
one page whose MediaBox matches the sheet size (297 x 167 mm), no-gate patterns
are matched against the PDF's own extracted text, and library/SHA256SUMS carries
a matching hash for every item's PDF, byte-for-byte.

This check never launches a browser and never re-renders. It cannot detect a
PDF that is out of date with a source that is not in this repository; do not
add a check that pretends to.

Usage: python3 scripts/check_library.py
Runs a self-test against throwaway fixtures in a temp directory before checking
the real tree - see .github/workflows/library.yml for the same shape.
"""
import hashlib
import os
import re
import shutil
import sys
import tempfile

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("check_library: pypdf is required (pip install pypdf)")

LIBRARY_DIR = "library"
CHECKSUMS_FILE = "SHA256SUMS"
NON_ITEM_ENTRIES = {"README.md", CHECKSUMS_FILE}
GEOMETRY_TOLERANCE_PT = 0.5
# Published sheet size. Read from the PDF's MediaBox, not from a source file.
PAGE_W_MM, PAGE_H_MM = 297.0, 167.0


def mm_to_pt(mm):
    return mm * 72.0 / 25.4


PAGE_W_PT, PAGE_H_PT = mm_to_pt(PAGE_W_MM), mm_to_pt(PAGE_H_MM)

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

    if os.path.isfile(source_path_for(library_root, slug)):
        errors.append(f"{slug_dir}: unexpected {slug}.source.html")

    expected_pdf = f"{slug}.pdf"
    if not os.path.isdir(slug_dir):
        return errors
    pdfs = [f for f in os.listdir(slug_dir) if f.lower().endswith(".pdf")]
    if expected_pdf not in pdfs:
        errors.append(f"{slug_dir}: missing {expected_pdf}")
    for f in pdfs:
        if f != expected_pdf:
            errors.append(f"{slug_dir}: PDF named {f!r}, expected only {expected_pdf!r}")
    return errors


def read_pdf(pdf_path):
    """Return (width_pt, height_pt, page_count, extracted_text), or an error string."""
    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        return f"{pdf_path}: cannot read PDF ({e})"
    page_count = len(reader.pages)
    if page_count == 0:
        return f"{pdf_path}: no pages"
    box = reader.pages[0].mediabox
    width = float(box.width)
    height = float(box.height)
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return width, height, page_count, "\n".join(texts)


def check_gate(library_root, slug):
    errors = []
    pdf_path = pdf_path_for(library_root, slug)
    if not os.path.isfile(pdf_path):
        return errors
    got = read_pdf(pdf_path)
    if isinstance(got, str):
        return [got]
    text = got[3]
    for pattern, label in GATE_PATTERNS:
        if pattern.search(text):
            errors.append(f"{pdf_path}: extracted text contains {label} - no gate is allowed on a library sheet")
    return errors


def check_geometry(library_root, slug):
    """Page count and MediaBox of the committed PDF - never by re-rendering."""
    pdf_path = pdf_path_for(library_root, slug)
    if not os.path.isfile(pdf_path):
        return []
    got = read_pdf(pdf_path)
    if isinstance(got, str):
        return [got]
    got_w_pt, got_h_pt, page_count, _text = got

    errors = []
    if page_count != 1:
        errors.append(f"{pdf_path}: expected exactly 1 page, found {page_count}")
    if abs(got_w_pt - PAGE_W_PT) > GEOMETRY_TOLERANCE_PT or abs(got_h_pt - PAGE_H_PT) > GEOMETRY_TOLERANCE_PT:
        errors.append(
            f"{pdf_path}: MediaBox {got_w_pt:.2f}x{got_h_pt:.2f}pt does not match "
            f"sheet size {PAGE_W_PT:.2f}x{PAGE_H_PT:.2f}pt "
            f"({PAGE_W_MM:g} x {PAGE_H_MM:g} mm, tolerance {GEOMETRY_TOLERANCE_PT}pt)"
        )
    return errors


def parse_checksums(checksums_path):
    """Returns {relative_path: lowercase_hex_sha256}, or None if the file is missing."""
    if not os.path.isfile(checksums_path):
        return None
    entries = {}
    with open(checksums_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.rstrip("\r\n")
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
    """Every item's PDF has a SHA256SUMS entry verified against the committed file."""
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
        rel = f"{slug}/{slug}.pdf"
        abs_path = pdf_path_for(library_root, slug)
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
        errors.extend(check_geometry(library_root, slug))
    errors.extend(check_checksums(library_root, slugs))
    return errors, slugs


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _pdf_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _fixture_pdf(w_pt=PAGE_W_PT, h_pt=PAGE_H_PT, page_count=1, text="Widgets"):
    """A small valid PDF with a MediaBox, extractable text, and a real xref."""
    escaped = _pdf_escape(text)
    objs = []
    kids = " ".join(f"{3 + i * 2} 0 R" for i in range(page_count))
    objs.append(f"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n".encode("ascii"))
    objs.append(f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {page_count} >>\nendobj\n".encode("ascii"))
    font_id = 3 + page_count * 2
    for i in range(page_count):
        page_id = 3 + i * 2
        contents_id = page_id + 1
        stream = f"BT /F1 12 Tf 72 72 Td ({escaped}) Tj ET\n".encode("ascii")
        objs.append(
            (
                f"{page_id} 0 obj\n"
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w_pt:.2f} {h_pt:.2f}] "
                f"/Contents {contents_id} 0 R "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>\n"
                f"endobj\n"
            ).encode("ascii")
        )
        objs.append(
            f"{contents_id} 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"endstream\nendobj\n"
        )
    objs.append(
        f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n".encode("ascii")
    )
    header = b"%PDF-1.4\n"
    offsets = [0]
    pos = len(header)
    for obj in objs:
        offsets.append(pos)
        pos += len(obj)
    n = len(offsets)
    xref = f"xref\n0 {n}\n0000000000 65535 f \n".encode("ascii")
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode("ascii")
    trailer = f"trailer\n<< /Size {n} /Root 1 0 R >>\nstartxref\n{pos}\n%%EOF\n".encode("ascii")
    return header + b"".join(objs) + xref + trailer


def _sha256sums_lines(root_for_hash, slug):
    pdf_path = pdf_path_for(os.path.join(root_for_hash, LIBRARY_DIR), slug)
    return f"{sha256_of(pdf_path)}  {slug}/{slug}.pdf\n"


def _fresh_item(tmp, slug="widgets", pdf_bytes=None):
    """A minimal, contract-clean item: <slug>.pdf and a matching SHA256SUMS entry."""
    pdf_path = pdf_path_for(os.path.join(tmp, LIBRARY_DIR), slug)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    with open(pdf_path, "wb") as f:
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

    tmp = tempfile.mkdtemp()
    try:
        _fresh_item(tmp)
        errors, slugs = run_checks(tmp)
        _expect(errors == [], "a contract-clean item passes with zero errors", "a clean item was flagged", failures)
    finally:
        shutil.rmtree(tmp)

    tmp = tempfile.mkdtemp()
    try:
        _write(os.path.join(tmp, LIBRARY_DIR, CHECKSUMS_FILE), "")
        errors, slugs = run_checks(tmp)
        _expect(errors == [] and slugs == [], "zero items present passes vacuously", "an empty library was flagged", failures)
    finally:
        shutil.rmtree(tmp)

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

    tmp = tempfile.mkdtemp()
    try:
        slug = _fresh_item(tmp)
        _write(source_path_for(os.path.join(tmp, LIBRARY_DIR), slug), "<html></html>")
        errors, _ = run_checks(tmp)
        _expect(
            any("unexpected widgets.source.html" in e for e in errors),
            "an item directory carrying <slug>.source.html is caught",
            "a leftover source was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    tmp = tempfile.mkdtemp()
    try:
        _fresh_item(tmp, pdf_bytes=_fixture_pdf(text="before you download paywall"))
        errors, _ = run_checks(tmp)
        _expect(
            any("interstitial/gate marker" in e for e in errors),
            "a PDF whose extracted text carries a gate pattern is caught",
            "a gate pattern in PDF text was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    tmp = tempfile.mkdtemp()
    try:
        _fresh_item(tmp, pdf_bytes=_fixture_pdf(text="subscribe via mailchimp"))
        errors, _ = run_checks(tmp)
        _expect(
            any("mail-capture/signup script" in e for e in errors),
            "a PDF whose extracted text names a signup script is caught",
            "a signup-script gate in PDF text was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    tmp = tempfile.mkdtemp()
    try:
        _fresh_item(tmp, pdf_bytes=_fixture_pdf(w_pt=PAGE_W_PT + 5))
        errors, _ = run_checks(tmp)
        _expect(
            any("does not match" in e and "MediaBox" in e for e in errors),
            "a PDF whose MediaBox disagrees with the sheet size is caught",
            "a geometry mismatch was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

    tmp = tempfile.mkdtemp()
    try:
        _fresh_item(tmp, pdf_bytes=_fixture_pdf(page_count=2))
        errors, _ = run_checks(tmp)
        _expect(
            any("expected exactly 1 page" in e for e in errors),
            "a PDF with more than one page is caught",
            "a page-count mismatch was not caught",
            failures,
        )
    finally:
        shutil.rmtree(tmp)

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

    tmp = tempfile.mkdtemp()
    try:
        _fresh_item(tmp)
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
        print(
            f"::error::check_library self-test failed - {len(failures)} check(s) did not "
            "behave as expected, not trusting its verdict on the real tree"
        )
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
